# Xinxin本地版启动脚本
# 纯本机运行：后端 127.0.0.1:8010，前端 127.0.0.1:5180（均只绑回环，不直接暴露）。
# 局域网直连：Caddy 网关监听 http://<本机局域网IP>:8080，手机连同一 WiFi 即可用，
#             无需域名、无需证书、无需公网 IP。首次使用可运行 ./Setup-Lan-Access.ps1
#             自动探测局域网 IP 并放行 Windows 防火墙。
# 用法：
#   ./Start-Xinxin-Local.ps1                # 本机 + 局域网直连（默认）
#   ./Start-Xinxin-Local.ps1 -NoBrowser     # 不自动打开浏览器
#   ./Start-Xinxin-Local.ps1 -NoGateway     # 不启动网关（仅本机 127.0.0.1 调试）
#   ./Start-Xinxin-Local.ps1 -GatewayPort 8080 -BackendPort 8010 -FrontendPort 5180
param(
  [switch]$NoBrowser,
  [switch]$NoGateway,
  [int]$GatewayPort = 8080,  # 局域网入口端口（手机用 http://<局域网IP>:<此端口>）
  [int]$BackendPort = 0,     # 0 = 读取 backend/.env 的 XINXIN_PORT
  [int]$FrontendPort = 0     # 0 = 读取 backend/.env 的 XINXIN_FRONTEND_PORT
)
$ErrorActionPreference='Stop'
$projectPath=$PSScriptRoot
$backendPath=Join-Path $projectPath 'backend'
$frontendPath=Join-Path $projectPath 'frontend'
$runtimePath=Join-Path $projectPath '.runtime'
$manifestPath=Join-Path $runtimePath 'processes.json'
$caddyfilePath=Join-Path $projectPath 'Caddyfile.local'
# 优先用 PATH 里的 caddy（winget install Caddy.Caddy 或官方下载），其次用 tools/caddy.exe
$caddyOnPath=Get-Command caddy -ErrorAction SilentlyContinue
$caddyExe=if($caddyOnPath){$caddyOnPath.Source}else{Join-Path $projectPath 'tools/caddy.exe'}
$gatewayEnvFile=Join-Path $runtimePath 'gateway.env'
New-Item -ItemType Directory -Force -Path $runtimePath | Out-Null
$script:instances=@()

function Get-EnvValue([string]$Key,[string]$Default){
  $envFile=Join-Path $backendPath '.env'
  if(Test-Path -LiteralPath $envFile){
    $found=Select-String -LiteralPath $envFile -Pattern "(?m)^\s*$Key=(.*)$" | Select-Object -First 1
    if($found -and $found.Matches[0].Groups[1].Value.Trim()){return $found.Matches[0].Groups[1].Value.Trim()}
  }
  return $Default
}
if($BackendPort -le 0){$BackendPort=[int](Get-EnvValue 'XINXIN_PORT' '8010')}
if($FrontendPort -le 0){$FrontendPort=[int](Get-EnvValue 'XINXIN_FRONTEND_PORT' '5180')}

# 局域网 IP：取有默认网关且状态为 Up 的网卡上的第一个 IPv4 地址
function Get-LanIp{
  try{
    $cfg=Get-NetIPConfiguration | Where-Object {$_.IPv4DefaultGateway -ne $null -and $_.NetAdapter.Status -eq 'Up'} | Select-Object -First 1
    if($cfg){return $cfg.IPv4Address.IPAddress}
  }catch{}
  return ''
}
$lanIp=Get-LanIp
$lanOrigin=if($lanIp){"http://${lanIp}:$GatewayPort"}else{''}

if(Test-Path -LiteralPath $manifestPath){
  $saved=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
  foreach($entry in $saved.services){
    $existing=Get-Process -Id $entry.id -ErrorAction SilentlyContinue
    if($existing -and $existing.StartTime.ToUniversalTime().Ticks -eq [long]$entry.start_ticks){$script:instances+=$entry}
  }
}
function Save-Instances {
  @{services=@($script:instances)} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
}
function Test-XinxinHealth([int]$Port){
  try{return (Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 3).status -eq 'ok'}catch{return $false}
}
# 各角色就绪判定：backend/frontend 看 /health；gateway 看端口是否已监听
$backendReady={Test-XinxinHealth $BackendPort}
$frontendReady={Test-XinxinHealth $FrontendPort}
$gatewayReady={
  $listener=Get-NetTCPConnection -LocalPort $GatewayPort -State Listen -ErrorAction SilentlyContinue
  return [bool]$listener
}
function Start-XinxinService([string]$Role,[string]$Executable,[string[]]$Arguments,[string]$Directory,[int]$Port,[scriptblock]$Ready){
  if(& $Ready){Write-Host "$Role already running on port $Port";return}
  $occupied=Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  if($occupied){throw "Port $Port is occupied by another application."}
  # Windows PowerShell 的 Start-Process 无法处理环境变量的大小写变体重复（如 HTTPS_PROXY 与 https_proxy 并存）；
  # 仅在检测到重复时临时收起小写变体，不影响正常环境，也不改子进程已继承的设置。
  $shadowedProxies=$false
  try{$null=Get-ChildItem -LiteralPath env: -ErrorAction Stop}catch{$shadowedProxies=$true}
  if($shadowedProxies){
    foreach($lower in 'http_proxy','https_proxy','all_proxy','no_proxy'){
      Remove-Item -LiteralPath "env:$lower" -ErrorAction SilentlyContinue
    }
  }
  $service=Start-Process -FilePath $Executable -ArgumentList $Arguments -WorkingDirectory $Directory -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimePath "$Role.out.log") -RedirectStandardError (Join-Path $runtimePath "$Role.err.log")
  $script:instances+=@{role=$Role;id=$service.Id;start_ticks=$service.StartTime.ToUniversalTime().Ticks}
  Save-Instances
  for($attempt=0;$attempt -lt 240;$attempt++){
    if(& $Ready){Write-Host "$Role ready on port $Port";return}
    if($service.HasExited){throw "$Role stopped. See $runtimePath/$Role.err.log"}
    Start-Sleep -Milliseconds 250
  }
  throw "$Role did not become ready. See $runtimePath/$Role.err.log"
}

# 1. 后端依赖
$pythonPath=Join-Path $backendPath '.venv/Scripts/python.exe'
if(-not(Test-Path -LiteralPath $pythonPath)){
  Push-Location -LiteralPath $backendPath
  try{python -m venv .venv;if($LASTEXITCODE -ne 0){throw 'Python 3.12+ is required'};& $pythonPath -m pip install -r requirements.lock;if($LASTEXITCODE -ne 0){throw 'Backend dependency installation failed'}}finally{Pop-Location}
}

# 2. 前端依赖与生产构建（缺资产或源码比构建产物新时自动重建）
function Test-FrontendBuild{
  $index=Join-Path $frontendPath 'dist/index.html'
  if(-not(Test-Path -LiteralPath $index)){return $false}
  $html=Get-Content -LiteralPath $index -Raw
  foreach($m in [regex]::Matches($html,'(?:src|href)="(/assets/[^"]+)"')){
    if(-not(Test-Path -LiteralPath ($frontendPath + '\dist' + $m.Groups[1].Value))){return $false}
  }
  # 只看 dist 是否存在会漏掉「改了源码但没重建」：产物比源文件旧就必须重建
  $built=(Get-Item -LiteralPath $index).LastWriteTimeUtc
  $sources=@(Get-ChildItem -LiteralPath (Join-Path $frontendPath 'src') -Recurse -File -ErrorAction SilentlyContinue)
  foreach($name in @('vite.config.ts','package.json','index.html')){
    $item=Get-Item -LiteralPath (Join-Path $frontendPath $name) -ErrorAction SilentlyContinue
    if($item){$sources+=$item}
  }
  foreach($item in $sources){
    if($item.LastWriteTimeUtc -gt $built.AddSeconds(2)){return $false}
  }
  return $true
}
Push-Location -LiteralPath $frontendPath
try{
  if(-not(Test-Path -LiteralPath 'node_modules/vite/bin/vite.js')){npm.cmd ci;if($LASTEXITCODE -ne 0){throw 'Frontend dependency installation failed'}}
  if(-not(Test-FrontendBuild)){Write-Host 'Building frontend (local edition)...';npm.cmd run build;if($LASTEXITCODE -ne 0){throw 'Frontend production build failed'}}
}finally{Pop-Location}

# 3. 启动后端（只绑回环；CORS 额外放行局域网入口，保证手机 app 直连时跨源通过）
$oldData=$env:XINXIN_DATA_DIR
$oldCors=$env:XINXIN_CORS_ORIGINS
try{
  $env:XINXIN_DATA_DIR=Join-Path $backendPath 'data'
  $origins=Get-EnvValue 'XINXIN_CORS_ORIGINS' 'http://localhost:5180,http://127.0.0.1:5180,http://localhost:8080,http://127.0.0.1:8080,capacitor://localhost'
  if($lanOrigin -and ($origins -split ',').Trim() -notcontains $lanOrigin){$origins="$origins,$lanOrigin"}
  $env:XINXIN_CORS_ORIGINS=$origins
  Start-XinxinService 'backend' $pythonPath @('-X','utf8','-m','uvicorn','app.main:app','--host','127.0.0.1','--port',"$BackendPort",'--workers','1','--no-access-log') $backendPath $BackendPort $backendReady
}finally{$env:XINXIN_DATA_DIR=$oldData;$env:XINXIN_CORS_ORIGINS=$oldCors}

# 4. 启动前端（只绑回环；preview 代理 /api、/health 到后端）
$env:XINXIN_BACKEND_PORT="$BackendPort"
$nodePath=(Get-Command node.exe).Source
Start-XinxinService 'frontend' $nodePath @('node_modules/vite/bin/vite.js','preview','--host','127.0.0.1','--port',"$FrontendPort",'--strictPort') $frontendPath $FrontendPort $frontendReady

# 5. 局域网网关（Caddy 纯 HTTP 单入口）：未安装 caddy 则跳过并提示
$gatewayStarted=$false
if($NoGateway){
  Write-Host '已按 -NoGateway 跳过网关（仅本机 127.0.0.1 访问）'
}elseif(-not((Test-Path -LiteralPath $caddyExe) -and (Test-Path -LiteralPath $caddyfilePath))){
  Write-Host '网关未启动：未找到 caddy（PATH 或 tools/caddy.exe）'
  Write-Host '  手机直连需要网关；本机调试可加 -NoGateway。安装 Caddy：https://caddyserver.com/download（Windows amd64 标准版，无需插件），或 winget install Caddy.Caddy'
}else{
  # 网关 envfile 每次启动重写：端口与日志目录以脚本参数为准（父环境变量优先，避免旧文件干扰）
  $envLines=@(
    "# Xinxin本地版 局域网网关配置（由 Start-Xinxin-Local.ps1 自动生成，请勿手改）",
    "XINXIN_GATEWAY_PORT=$GatewayPort",
    "XINXIN_LOG_DIR=$(Join-Path $projectPath 'logs')"
  )
  [System.IO.File]::WriteAllLines($gatewayEnvFile,$envLines,(New-Object System.Text.UTF8Encoding($false)))
  $oldLogDir=$env:XINXIN_LOG_DIR
  $oldPort=$env:XINXIN_GATEWAY_PORT
  try{
    # 访问日志收在项目 logs，不写系统目录
    $env:XINXIN_LOG_DIR=Join-Path $projectPath 'logs'
    $env:XINXIN_GATEWAY_PORT="$GatewayPort"
    New-Item -ItemType Directory -Force -Path $env:XINXIN_LOG_DIR | Out-Null
    Start-XinxinService 'gateway' $caddyExe @('run','--config',$caddyfilePath,'--adapter','caddyfile','--envfile',$gatewayEnvFile) $projectPath $GatewayPort $gatewayReady
    $gatewayStarted=$true
  }finally{$env:XINXIN_LOG_DIR=$oldLogDir;$env:XINXIN_GATEWAY_PORT=$oldPort}
}

Write-Host ''
Write-Host 'Xinxin本地版 已启动'
Write-Host "  本机浏览器:    http://127.0.0.1:$FrontendPort"
if($gatewayStarted -and $lanIp){
  Write-Host "  手机/局域网:   http://${lanIp}:$GatewayPort   （手机需连同一 WiFi）"
  Write-Host "  如手机连不上：以管理员运行 ./Setup-Lan-Access.ps1 放行防火墙，或换 -GatewayPort"
}elseif($gatewayStarted){
  Write-Host "  手机/局域网:   http://<本机局域网IP>:$GatewayPort   （未能自动探测局域网 IP）"
}
Write-Host "  停止: ./Stop-Xinxin-Local.ps1"

# 防火墙自检：没有放行规则时，手机必然连不上局域网网关
if($gatewayStarted){
  $fwRuleName="Xinxin本地版网关 (TCP $GatewayPort)"
  $hasFwRule=$false
  try{$hasFwRule=[bool](Get-NetFirewallRule -DisplayName $fwRuleName -ErrorAction SilentlyContinue)}catch{$hasFwRule=$false}
  if(-not $hasFwRule){
    Write-Host ''
    Write-Host '[!] 手机多半连不上：Windows 防火墙尚未放行 TCP ' -NoNewline -ForegroundColor Yellow
    Write-Host $GatewayPort -ForegroundColor Yellow
    Write-Host '    以管理员身份运行 ./Setup-Lan-Access.ps1（或双击 放行局域网防火墙.cmd）放行一次。'
    $netCategory=''
    try{
      $prof=Get-NetConnectionProfile -ErrorAction Stop |
        Where-Object {$_.IPv4Connectivity -ne 'None'} | Select-Object -First 1
      if($prof){$netCategory=$prof.NetworkCategory}
    }catch{}
    if($netCategory -eq 'Public'){
      Write-Host '    另：当前 Wi-Fi 被识别为「公用网络」，入站拦截更严，建议改为专用网络：'
      Write-Host '      设置 → 网络和 Internet → Wi-Fi → 点击当前网络 → 网络配置文件类型 → 专用'
    }
  }
}
if(-not $NoBrowser){Start-Process "http://127.0.0.1:$FrontendPort"}
