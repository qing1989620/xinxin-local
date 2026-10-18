# Xinxin Local Edition - public access over a reverse tunnel
#
# Exposes the local gateway (127.0.0.1:<LocalPort>) so a phone on mobile data
# or any outside network can reach this machine's backend.
#
# Two modes:
#   cloudflare (default) - quick tunnel, no account and no domain needed.
#                          Cloudflare assigns https://<random>.trycloudflare.com,
#                          which CHANGES on every restart. Good for validating the
#                          path, not for a permanent address.
#   frp                  - self-hosted relay via your own public server.
#                          Fixed address. Needs tools/frpc.exe and tools/frpc.toml.
#
# Usage:
#   ./Start-Tunnel.ps1
#   ./Start-Tunnel.ps1 -UseFrp
#   ./Start-Tunnel.ps1 -LocalPort 9090
param(
  [int]$LocalPort = 8080,
  [switch]$UseFrp
)
$ErrorActionPreference='Stop'
$projectPath=$PSScriptRoot
$runtimePath=Join-Path $projectPath '.runtime'
New-Item -ItemType Directory -Force -Path $runtimePath | Out-Null

# --- 1. the local gateway must already be running ---
$listener=Get-NetTCPConnection -LocalPort $LocalPort -State Listen -ErrorAction SilentlyContinue
if(-not $listener){
  throw "Nothing is listening on port $LocalPort. Run ./Start-Xinxin-Local.ps1 first."
}
Write-Host "Local gateway is listening on 127.0.0.1:$LocalPort"

# --- 2. locate the tunnel binary ---
if($UseFrp){
  $tunnelExe=Join-Path $projectPath 'tools/frpc.exe'
  $tunnelArgs=@('-c',(Join-Path $projectPath 'tools/frpc.toml'))
  $missing='tools/frpc.exe (https://github.com/fatedier/frp/releases) or tools/frpc.toml'
}else{
  $found=Get-Command cloudflared -ErrorAction SilentlyContinue
  if($found){ $tunnelExe=$found.Source } else { $tunnelExe=Join-Path $projectPath 'tools/cloudflared.exe' }
  $tunnelArgs=@('tunnel','--url',"http://127.0.0.1:$LocalPort",'--no-autoupdate')
  $missing='tools/cloudflared.exe (https://github.com/cloudflare/cloudflared/releases)'
}

if(-not (Test-Path -LiteralPath $tunnelExe)){
  Write-Host ''
  Write-Host "Tunnel binary not found. Install $missing" -ForegroundColor Yellow
  if(-not $UseFrp){
    Write-Host '  winget install --id Cloudflare.cloudflared -e'
  }
  exit 1
}

$outLog=Join-Path $runtimePath 'tunnel.out.log'
$errLog=Join-Path $runtimePath 'tunnel.err.log'
foreach($f in @($outLog,$errLog)){ if(Test-Path -LiteralPath $f){ Remove-Item -LiteralPath $f -Force -ErrorAction SilentlyContinue } }

$proc=Start-Process -FilePath $tunnelExe -ArgumentList $tunnelArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput $outLog -RedirectStandardError $errLog
@{role='tunnel';id=$proc.Id;started=(Get-Date).ToString('s')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimePath 'tunnel.json') -Encoding UTF8

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
  Write-Host 'Xinxin is reachable from the public internet:' -ForegroundColor Green
  Write-Host "  $publicUrl"
  Write-Host ''
  Write-Host '  IMPORTANT: add the address above to XINXIN_CORS_ORIGINS in backend/.env'
  Write-Host '  and restart the backend, otherwise the phone page loads but API'
  Write-Host '  requests are blocked by the browser (CORS).'
  Write-Host ''
  Write-Host '  The quick-tunnel address changes on every restart. For a permanent'
  Write-Host '  address use a named Cloudflare Tunnel with your own domain, or frp.'
  Write-Host '  Close the tunnel with ./Stop-Xinxin-Local.ps1 (stops managed roles).'
}else{
  Write-Host 'No tunnel address within 45s. Check .runtime/tunnel.out.log and tunnel.err.log' -ForegroundColor DarkYellow
}
