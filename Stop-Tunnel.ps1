param([switch]$All)
$ErrorActionPreference='Stop'
$projectPath=$PSScriptRoot
$runtimePath=Join-Path $projectPath '.runtime'

. (Join-Path $projectPath 'desktop/Tunnel-State.ps1')
if(Stop-XinxinTunnel $runtimePath){
  Write-Host 'Stopped the managed Xinxin tunnel; the public entry is closed.'
}else{
  Write-Host 'No verified Xinxin tunnel was running; other processes were preserved.'
}

# -All also stops backend / frontend / gateway.
if ($All) {
  $stop = Join-Path $projectPath 'Stop-Xinxin-Local.ps1'
  if (Test-Path -LiteralPath $stop) { & $stop }
}
