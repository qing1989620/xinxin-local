# Xinxin Local Edition - public access over a reverse tunnel
#
# Exposes the local gateway (127.0.0.1:<LocalPort>) so a phone on mobile data
# or any outside network can reach this machine's backend.
#
# Quick tunnel only: no account, no domain, and no server to rent. Cloudflare
# assigns https://<random>.trycloudflare.com, which changes on every restart.
# The LAN address (http://<this-machine-ip>:8080) is the stable one.
#
# Usage:
#   ./Start-Tunnel.ps1
#   ./Start-Tunnel.ps1 -LocalPort 9090
param(
  [int]$LocalPort = 8080
)
$ErrorActionPreference='Stop'
$projectPath=$PSScriptRoot
$runtimePath=Join-Path $projectPath '.runtime'
. (Join-Path $projectPath 'desktop/Local-ServiceState.ps1')
. (Join-Path $projectPath 'desktop/Tunnel-State.ps1')
New-Item -ItemType Directory -Force -Path $runtimePath | Out-Null

# --- 1. the local gateway must already be running ---
if(-not(Test-XinxinHealth $LocalPort)){
  throw "The Xinxin gateway is not healthy on port $LocalPort. Run ./Start-Xinxin-Local.ps1 first."
}
$manifestPath=Join-Path $runtimePath 'processes.json'
if(-not(Test-Path -LiteralPath $manifestPath)){throw 'No managed Xinxin gateway identity; public access was not started.'}
$services=Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$gateway=@($services.services | Where-Object {$_.role -eq 'gateway'}) | Select-Object -First 1
$instance=if($gateway){Get-Process -Id $gateway.id -ErrorAction SilentlyContinue}else{$null}
if(-not $instance -or $instance.StartTime.ToUniversalTime().Ticks -ne [long]$gateway.start_ticks -or -not(Test-XinxinManagedPort $instance.Id $LocalPort)){
  throw 'The listener is not this project managed gateway; public access was not started.'
}
Write-Host "Local gateway is listening on 127.0.0.1:$LocalPort"

# --- 2. locate the tunnel binary ---
$found=Get-Command cloudflared -ErrorAction SilentlyContinue
if($found){ $tunnelExe=$found.Source } else { $tunnelExe=Join-Path $projectPath 'tools/cloudflared.exe' }
$tunnelArgs=@('tunnel','--url',"http://127.0.0.1:$LocalPort",'--no-autoupdate')
$missing='tools/cloudflared.exe (https://github.com/cloudflare/cloudflared/releases)'

if(-not (Test-Path -LiteralPath $tunnelExe)){
  Write-Host ''
  Write-Host "Tunnel binary not found. Install $missing" -ForegroundColor Yellow
  Write-Host '  winget install --id Cloudflare.cloudflared -e'
  exit 1
}

$stopped = Stop-XinxinTunnel $runtimePath
if($stopped){Write-Host 'Stopped the previously managed project tunnel.'}

$outLog=Join-Path $runtimePath 'tunnel.out.log'
$errLog=Join-Path $runtimePath 'tunnel.err.log'
foreach($f in @($outLog,$errLog)){ if(Test-Path -LiteralPath $f){ Remove-Item -LiteralPath $f -Force -ErrorAction SilentlyContinue } }

# Windows PowerShell Start-Process fails when duplicate env vars differ only in
# case (http_proxy vs HTTP_PROXY). Detect it and drop the lowercase variants.
$shadowedProxies=$false
try{$null=Get-ChildItem -LiteralPath env: -ErrorAction Stop}catch{$shadowedProxies=$true}
if($shadowedProxies){
  foreach($lower in 'http_proxy','https_proxy','all_proxy','no_proxy'){
    Remove-Item -LiteralPath "env:$lower" -ErrorAction SilentlyContinue
  }
}

$proc=Start-Process -FilePath $tunnelExe -ArgumentList $tunnelArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput $outLog -RedirectStandardError $errLog
@{role='tunnel';id=$proc.Id;start_ticks=$proc.StartTime.ToUniversalTime().Ticks;executable=[System.IO.Path]::GetFullPath($tunnelExe);local_port=$LocalPort} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimePath 'tunnel.json') -Encoding UTF8

Write-Host "Tunnel started (PID=$($proc.Id)); waiting for a public address..."
$publicUrl=''
for($i=0;$i -lt 90;$i++){
  Start-Sleep -Milliseconds 500
  foreach($f in @($outLog,$errLog)){
    if(Test-Path -LiteralPath $f){
      $txt=Get-Content -LiteralPath $f -Raw -ErrorAction SilentlyContinue
      if($txt){
        $m=[regex]::Match($txt,'https://[A-Za-z0-9\-]+\.trycloudflare\.com')
        if($m.Success){ $publicUrl=$m.Value }
      }
    }
  }
  if($publicUrl){ break }
}

Write-Host ''
if($publicUrl){
  # remember the address for other tools and for the stop script.
  # Write without a BOM: the backend reads this file as a strict URL.
  $urlFile=Join-Path $runtimePath 'public-url.txt'
  [System.IO.File]::WriteAllText($urlFile, $publicUrl, (New-Object System.Text.UTF8Encoding($false)))
  # The website and API share the tunnel origin. Starting a tunnel does not
  # require rewriting credentials/configuration or restarting active services.

  Write-Host 'Xinxin is reachable from the public internet:' -ForegroundColor Green
  Write-Host "  $publicUrl"
  $lanUrl=''
  try{
    $addresses=Get-Content -LiteralPath (Join-Path $runtimePath 'addresses.json') -Raw | ConvertFrom-Json
    $lanUrl=$addresses.lan
  }catch{}
  if($lanUrl){
    Write-Host ''
    Write-Host "  Same Wi-Fi, no server, never changes: $lanUrl"
  }
  Write-Host '  The quick-tunnel address changes on every restart; the LAN address does not.'
}else{
  $null = Stop-XinxinTunnel $runtimePath
  throw 'No tunnel address within 45s; managed tunnel stopped. Check .runtime/tunnel.out.log and tunnel.err.log.'
}
