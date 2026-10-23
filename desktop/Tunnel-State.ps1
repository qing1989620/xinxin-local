# Stop only the process whose identity was recorded by this project.
function Stop-XinxinTunnel([string]$RuntimePath) {
  $manifest = Join-Path $RuntimePath 'tunnel.json'
  if (-not (Test-Path -LiteralPath $manifest)) { return $false }
  $entry = Get-Content -LiteralPath $manifest -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($entry.role -ne 'tunnel' -or -not $entry.id -or -not $entry.start_ticks -or -not $entry.executable) {
    throw 'Cannot verify the saved tunnel identity; all processes and its manifest were preserved.'
  }
  $instance = Get-Process -Id $entry.id -ErrorAction SilentlyContinue
  $stopped = $false
  if ($instance -and $instance.StartTime.ToUniversalTime().Ticks -eq [long]$entry.start_ticks) {
    if (-not $instance.Path -or [System.IO.Path]::GetFullPath($instance.Path) -ne [System.IO.Path]::GetFullPath($entry.executable)) {
      throw 'Tunnel executable identity differs; process and manifest were preserved.'
    }
    $instance.Kill()
    if (-not $instance.WaitForExit(10000)) { throw 'The managed tunnel did not stop; manifest was preserved.' }
    $stopped = $true
  }
  # A reused PID belongs to somebody else. Remove only our stale metadata.
  Remove-Item -LiteralPath $manifest -Force
  $urlFile = Join-Path $RuntimePath 'public-url.txt'
  if (Test-Path -LiteralPath $urlFile) { Remove-Item -LiteralPath $urlFile -Force }
  return $stopped
}
