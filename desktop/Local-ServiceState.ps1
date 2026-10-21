# Shared local startup checks. Keep helpers free of startup side effects.
function Get-XinxinFileHash([string]$Path) {
  $algorithm = [System.Security.Cryptography.SHA256]::Create()
  try { return [System.BitConverter]::ToString($algorithm.ComputeHash([System.IO.File]::ReadAllBytes($Path))).Replace('-', '') }
  finally { $algorithm.Dispose() }
}

function Get-XinxinHealth([int]$Port) {
  try {
    $request = [System.Net.WebRequest]::Create("http://127.0.0.1:$Port/health")
    $request.Proxy = $null
    $request.Timeout = 3000
    $response = $request.GetResponse()
    try {
      $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
      try { return ($reader.ReadToEnd() | ConvertFrom-Json) } finally { $reader.Dispose() }
    } finally { $response.Dispose() }
  } catch { return $null }
}

function Test-XinxinHealth([int]$Port, [string]$ExpectedBuild = '') {
  $health = Get-XinxinHealth $Port
  return ($health -and $health.status -eq 'ok' -and $health.product -eq 'Xinxin' -and (-not $ExpectedBuild -or $health.build -eq $ExpectedBuild))
}

function Test-XinxinManagedBuild($Entry, [string]$Fingerprint) {
  return ($Entry -and $Entry.fingerprint -and $Entry.fingerprint -eq $Fingerprint)
}

function Test-XinxinManagedPort([int]$ProcessId, [int]$Port) {
  # Windows venv python.exe may be a launcher whose child owns the socket.
  $root = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
  if (-not $root) { return $false }
  $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
  foreach ($listener in $listeners) {
    $ancestor = [int]$listener.OwningProcess
    $visited = @{}
    $childStarted = $null
    for ($depth = 0; $depth -lt 32 -and $ancestor -gt 0; $depth++) {
      if ($visited.ContainsKey($ancestor)) { break }
      $visited[$ancestor] = $true
      $process = Get-Process -Id $ancestor -ErrorAction SilentlyContinue
      if (-not $process -or $process.StartTime -lt $root.StartTime) { break }
      if ($childStarted -and $process.StartTime -gt $childStarted) { break }
      if ($ancestor -eq $ProcessId) { return $true }
      $childStarted = $process.StartTime
      try { $details = Get-CimInstance Win32_Process -Filter "ProcessId=$ancestor" -ErrorAction Stop }
      catch { break }
      if (-not $details) { break }
      $ancestor = [int]$details.ParentProcessId
    }
  }
  return $false
}

function Test-XinxinDesktopBuild([string]$Project, [string]$Profile) {
  $indexPath = Join-Path $Project 'frontend/dist/index.html'
  $stampPath = Join-Path $Profile 'build-stamp.txt'
  if (-not (Test-Path -LiteralPath $indexPath) -or -not (Test-Path -LiteralPath $stampPath)) { return $false }
  $stamp = (Get-Content -LiteralPath $stampPath -Raw).Trim()
  return $stamp -eq (Get-XinxinFileHash $indexPath)
}
