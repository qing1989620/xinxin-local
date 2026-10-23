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

function Test-XinxinApplicationBlocked([System.Exception]$Failure) {
  # A blocked optional gateway must not prevent the loopback desktop app from
  # opening. Do not suppress port/configuration errors or change OS policy.
  for ($depth = 0; $Failure -and $depth -lt 16; $depth++) {
    if ($Failure -is [System.ComponentModel.Win32Exception] -and $Failure.NativeErrorCode -eq 4551) { return $true }
    $Failure = $Failure.InnerException
  }
  return $false
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

# PowerShell 5.1 promotes redirected native stderr to ErrorRecord objects.
# Build warnings are output; the native exit code decides success.
function Invoke-XinxinNative([string]$Executable, [string[]]$Arguments, [string]$FailureMessage) {
  $command = Get-Command -Name $Executable -CommandType Application -ErrorAction Stop
  $previousPreference = $ErrorActionPreference
  $previousEncoding = [Console]::OutputEncoding
  try {
    $ErrorActionPreference = 'Continue'
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    & $command.Source @Arguments 2>&1 | ForEach-Object { Write-Output $_.ToString() }
    $nativeExit = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $previousPreference
    [Console]::OutputEncoding = $previousEncoding
  }
  if ($nativeExit -ne 0) { throw "$FailureMessage (exit $nativeExit)" }
}
