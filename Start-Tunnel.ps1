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

# A previous quick tunnel would stay alive with its own (now stale) address and
# keep consuming a connection. Only one public entry should exist at a time.
$existing=Get-Process -Name cloudflared -ErrorAction SilentlyContinue
if($existing){
  $existing | Stop-Process -Force -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 2
  Write-Host "Stopped $($existing.Count) previous tunnel process(es)."
}

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
  # remember the address for other tools and for the stop script
  Set-Content -LiteralPath (Join-Path $runtimePath 'public-url.txt') -Value $publicUrl -Encoding UTF8
  # quick-tunnel origins change every run: drop the stale one, append the new one
  $envFile=Join-Path $projectPath 'backend/.env'
  if(Test-Path -LiteralPath $envFile){
    $lines=Get-Content -LiteralPath $envFile
    $updated=New-Object System.Collections.Generic.List[string]
    $found=$false
    foreach($line in $lines){
      if($line -match '^\s*XINXIN_CORS_ORIGINS='){
        $value=$line.Substring($line.IndexOf('=')+1)
        $kept=@()
        foreach($part in ($value -split ',')){
          $p=$part.Trim()
          if($p -and ($p -notmatch 'trycloudflare\.com')){ $kept+=$p }
        }
        $kept+=$publicUrl
        $updated.Add('XINXIN_CORS_ORIGINS=' + ($kept -join ','))
        $found=$true
      }else{
        $updated.Add($line)
      }
    }
    if(-not $found){ $updated.Add('XINXIN_CORS_ORIGINS=' + $publicUrl) }
    [System.IO.File]::WriteAllLines($envFile,$updated,(New-Object System.Text.UTF8Encoding($false)))
    Write-Host '  backend/.env CORS allowlist updated.'

    # restart managed services so the backend serves the new origin.
    # Do NOT use *> here: the launcher sets $ErrorActionPreference='Stop', and
    # merging a native command's stderr into the stream aborts it mid-way.
    Write-Host '  Restarting local services so the new origin takes effect...'
    & (Join-Path $projectPath 'Stop-Xinxin-Local.ps1')
    Start-Sleep -Seconds 2
    & (Join-Path $projectPath 'Start-Xinxin-Local.ps1') -NoBrowser
    Start-Sleep -Seconds 6
  }

  Write-Host 'Xinxin is reachable from the public internet:' -ForegroundColor Green
  Write-Host "  $publicUrl"
  Write-Host ''
  Write-Host '  The quick-tunnel address changes on every restart. For a permanent'
  Write-Host '  address use a named Cloudflare Tunnel with your own domain, or frp.'
}else{
  Write-Host 'No tunnel address within 45s. Check .runtime/tunnel.out.log and tunnel.err.log' -ForegroundColor DarkYellow
}
