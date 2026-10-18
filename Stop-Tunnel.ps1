param([switch]$All)
$ErrorActionPreference='Stop'
$projectPath=$PSScriptRoot
$runtimePath=Join-Path $projectPath '.runtime'

# Stop the public-access tunnel (cloudflared).
$procs = Get-Process -Name cloudflared -ErrorAction SilentlyContinue
if ($procs) {
  $procs | Stop-Process -Force
  Write-Host "已停止 $($procs.Count) 个 cloudflared 进程（公网入口已关闭）"
} else {
  Write-Host '没有正在运行的 cloudflared 进程'
}

$json = Join-Path $runtimePath 'tunnel.json'
if (Test-Path -LiteralPath $json) {
  Remove-Item -LiteralPath $json -Force -ErrorAction SilentlyContinue
}

# -All also stops backend / frontend / gateway.
if ($All) {
  $stop = Join-Path $projectPath 'Stop-Xinxin-Local.ps1'
  if (Test-Path -LiteralPath $stop) { & $stop }
}
