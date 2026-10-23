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
  [int]$FrontendPort = 0,    # 0 = 读取 backend/.env 的 XINXIN_FRONTEND_PORT
  [string]$DataDirectory = '',
  [string]$RuntimeDirectory = '',
  [string]$FrontendBuildDirectory = ''
)
$ErrorActionPreference='Stop'
$projectPath=$PSScriptRoot
$backendPath=Join-Path $projectPath 'backend'
$frontendPath=Join-Path $projectPath 'frontend'
$frontendBuildPath=Join-Path $frontendPath 'dist'
if($FrontendBuildDirectory){
  $requestedBuild=[System.IO.Path]::GetFullPath($FrontendBuildDirectory)
  $testBuildRoot=[System.IO.Path]::GetFullPath((Join-Path $frontendPath '.qa-data')).TrimEnd('\') + '\'
  if(-not $requestedBuild.StartsWith($testBuildRoot,[System.StringComparison]::OrdinalIgnoreCase)){
    throw 'Custom frontend builds must stay inside frontend/.qa-data; the existing build was preserved.'
  }
  $frontendBuildPath=$requestedBuild
}
$runtimePath=Join-Path $projectPath '.runtime'
if($RuntimeDirectory){$runtimePath=[System.IO.Path]::GetFullPath($RuntimeDirectory)}
if(-not $DataDirectory){$DataDirectory=Join-Path $backendPath 'data'}
$DataDirectory=[System.IO.Path]::GetFullPath($DataDirectory)
. (Join-Path $projectPath 'desktop/Local-ServiceState.ps1')
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
$lanIp=if($NoGateway){''}else{Get-LanIp}
$lanOrigin=if($lanIp){"http://${lanIp}:$GatewayPort"}else{''}

if(Test-Path -LiteralPath $manifestPath){
  $saved=Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
  foreach($entry in $saved.services){
    $existing=Get-Process -Id $entry.id -ErrorAction SilentlyContinue
    if($existing -and $existing.StartTime.ToUniversalTime().Ticks -eq [long]$entry.start_ticks){$script:instances+=$entry}
  }
}
function Save-Instances {
  @{services=@($script:instances)} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
}
# 各角色就绪判定：backend/frontend 看 /health；gateway 看端口是否已监听
$backendReady={Test-XinxinHealth $BackendPort $backendBuild}
$frontendReady={Test-XinxinHealth $FrontendPort $backendBuild}
$gatewayReady={
  $listener=Get-NetTCPConnection -LocalPort $GatewayPort -State Listen -ErrorAction SilentlyContinue
  return [bool]$listener
}
function Start-XinxinService([string]$Role,[string]$Executable,[string[]]$Arguments,[string]$Directory,[int]$Port,[scriptblock]$Ready,[string]$Fingerprint=''){
  $owned=@($script:instances | Where-Object {$_.role -eq $Role}) | Select-Object -First 1
  $instance=if($owned){Get-Process -Id $owned.id -ErrorAction SilentlyContinue}else{$null}
  $managedAlive=$instance -and $instance.StartTime.ToUniversalTime().Ticks -eq [long]$owned.start_ticks
  if($managedAlive){
    if($owned.port -and [int]$owned.port -ne $Port){throw "Managed $Role port differs from this request; the running service was preserved."}
    if(-not $owned.port){
      if(-not(Test-XinxinManagedPort $instance.Id $Port)){throw "Cannot verify the managed $Role port; the running service was preserved."}
    }
    if($Role -eq 'backend'){
      $ownedData=[string]$owned.data_directory
      if(-not $ownedData){
        # Released legacy launchers had no custom directories and always set
        # XINXIN_DATA_DIR to backend/data. Only migrate that exact old contract.
        $legacyDefault=-not $owned.fingerprint -and $runtimePath -eq (Join-Path $projectPath '.runtime') -and $DataDirectory -eq (Join-Path $backendPath 'data')
        if(-not $legacyDefault){throw 'Cannot verify the managed backend data directory; the running service was preserved.'}
        $ownedData=Join-Path $backendPath 'data'
      }
      if([System.IO.Path]::GetFullPath($ownedData) -ne $DataDirectory){throw 'Managed backend data directory differs from this request; the running service was preserved.'}
    }
  }
  $serviceHealthy=& $Ready
  if($serviceHealthy -and $managedAlive -and (-not $Fingerprint -or (Test-XinxinManagedBuild $owned $Fingerprint))){Write-Host "$Role already running on port $Port (current build)";return}
  # The health request can outlive a crashing process. Recheck before consulting
  # stale database task rows or attempting to stop the managed process.
  $instance=if($owned){Get-Process -Id $owned.id -ErrorAction SilentlyContinue}else{$null}
  $managedAlive=$instance -and $instance.StartTime.ToUniversalTime().Ticks -eq [long]$owned.start_ticks
  if($owned){
    if($managedAlive){
      if($Role -eq 'backend'){
        $active=& $pythonPath (Join-Path $backendPath 'scripts/local_runtime.py') active-tasks $ownedData
        if($LASTEXITCODE -ne 0){throw 'Cannot verify active tasks; the running backend was preserved.'}
        if([int]$active -gt 0){throw 'Xinxin has active tasks. Finish or stop them before updating; the running service was preserved.'}
      }
      & (Join-Path $env:SystemRoot 'System32/taskkill.exe') /PID $instance.Id /T /F | Out-Null
      if($LASTEXITCODE -ne 0){throw "Could not stop the managed $Role process tree"}
      Write-Host "Updating managed $Role to the current build..."
    }
    $script:instances=@($script:instances | Where-Object {$_.id -ne $owned.id})
    Save-Instances
    for($i=0;$i -lt 40;$i++){
      if(-not(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)){break}
      Start-Sleep -Milliseconds 100
    }
  }
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
  $script:instances+=@{role=$Role;id=$service.Id;start_ticks=$service.StartTime.ToUniversalTime().Ticks;fingerprint=$Fingerprint;port=$Port;data_directory=$(if($Role -eq 'backend'){$DataDirectory}else{''})}
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
  try{Invoke-XinxinNative 'python' @('-m','venv','.venv') 'Python 3.12+ is required';Invoke-XinxinNative $pythonPath @('-m','pip','install','-r','requirements.lock') 'Backend dependency installation failed'}finally{Pop-Location}
}
# Existing installations also need new OCR/PDF dependencies. First check exact
# lock pins offline. Never mutate a venv while an unknown or busy backend uses it.
& $pythonPath (Join-Path $backendPath 'scripts/local_runtime.py') check-dependencies
if($LASTEXITCODE -ne 0){
  $ownedBackend=@($script:instances | Where-Object {$_.role -eq 'backend'}) | Select-Object -First 1
  $runningBackend=if($ownedBackend){Get-Process -Id $ownedBackend.id -ErrorAction SilentlyContinue}else{$null}
  $managedBackend=$runningBackend -and $runningBackend.StartTime.ToUniversalTime().Ticks -eq [long]$ownedBackend.start_ticks
  if($managedBackend){
    $ownedData=[string]$ownedBackend.data_directory
    if(-not $ownedData -and -not $ownedBackend.fingerprint -and $runtimePath -eq (Join-Path $projectPath '.runtime') -and $DataDirectory -eq (Join-Path $backendPath 'data')){$ownedData=$DataDirectory}
    if(-not $ownedData -or [System.IO.Path]::GetFullPath($ownedData) -ne $DataDirectory){throw 'Cannot verify the backend data directory for dependency synchronization; service preserved.'}
    if(($ownedBackend.port -and [int]$ownedBackend.port -ne $BackendPort) -or -not(Test-XinxinManagedPort $runningBackend.Id $BackendPort)){throw 'Cannot verify the backend port for dependency synchronization; service preserved.'}
    $active=& $pythonPath (Join-Path $backendPath 'scripts/local_runtime.py') active-tasks $ownedData
    if($LASTEXITCODE -ne 0 -or [int]$active -gt 0){throw 'Finish active tasks before dependency synchronization; service preserved.'}
    & (Join-Path $env:SystemRoot 'System32/taskkill.exe') /PID $runningBackend.Id /T /F | Out-Null
    if($LASTEXITCODE -ne 0){throw 'Could not stop the managed backend for dependency synchronization.'}
    $script:instances=@($script:instances | Where-Object {$_.id -ne $ownedBackend.id})
    Save-Instances
  }
  if(Get-NetTCPConnection -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue){throw 'Backend port is occupied; dependency synchronization was not attempted.'}
  Push-Location -LiteralPath $backendPath
  try{
    Invoke-XinxinNative $pythonPath @('-m','pip','install','-r','requirements.lock') 'Backend dependency synchronization failed'
    Invoke-XinxinNative $pythonPath @('scripts/local_runtime.py','check-dependencies') 'Backend dependency verification failed'
  }finally{Pop-Location}
}
$backendBuild=& $pythonPath (Join-Path $backendPath 'scripts/local_runtime.py') fingerprint
if($LASTEXITCODE -ne 0 -or -not $backendBuild){throw 'Cannot identify the backend build.'}

# 2. 前端依赖与生产构建（缺资产或源码比构建产物新时自动重建）
function Test-FrontendBuild{
  $index=Join-Path $frontendBuildPath 'index.html'
  if(-not(Test-Path -LiteralPath $index)){return $false}
  $html=Get-Content -LiteralPath $index -Raw
  foreach($m in [regex]::Matches($html,'(?:src|href)="(/assets/[^"]+)"')){
    if(-not(Test-Path -LiteralPath ($frontendBuildPath + $m.Groups[1].Value))){return $false}
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
  if(-not(Test-Path -LiteralPath 'node_modules/vite/bin/vite.js')){Invoke-XinxinNative 'npm.cmd' @('ci') 'Frontend dependency installation failed'}
  if(-not(Test-FrontendBuild)){Write-Host 'Building frontend (local edition)...';Invoke-XinxinNative 'npm.cmd' @('run','build','--','--outDir',$frontendBuildPath) 'Frontend production build failed'}
}finally{Pop-Location}

# 3. 启动后端（只绑回环；CORS 额外放行局域网入口，保证手机 app 直连时跨源通过）
$oldData=$env:XINXIN_DATA_DIR
$oldCors=$env:XINXIN_CORS_ORIGINS
try{
  $env:XINXIN_DATA_DIR=$DataDirectory
  $origins=Get-EnvValue 'XINXIN_CORS_ORIGINS' 'http://localhost:5180,http://127.0.0.1:5180,http://localhost:8080,http://127.0.0.1:8080,capacitor://localhost'
  if($lanOrigin -and ($origins -split ',').Trim() -notcontains $lanOrigin){$origins="$origins,$lanOrigin"}
  $env:XINXIN_CORS_ORIGINS=$origins
  Start-XinxinService 'backend' $pythonPath @('-X','utf8','-m','uvicorn','app.main:app','--host','127.0.0.1','--port',"$BackendPort",'--workers','1','--no-access-log') $backendPath $BackendPort $backendReady $backendBuild
}finally{$env:XINXIN_DATA_DIR=$oldData;$env:XINXIN_CORS_ORIGINS=$oldCors}

# 4. 启动前端（只绑回环；preview 代理 /api、/health 到后端）
$env:XINXIN_BACKEND_PORT="$BackendPort"
$nodePath=(Get-Command node.exe).Source
$frontendBuild=(Get-XinxinFileHash (Join-Path $frontendBuildPath 'index.html')) + ":$BackendPort"
if($FrontendBuildDirectory){$frontendBuild += ":$frontendBuildPath"}
Start-XinxinService 'frontend' $nodePath @('node_modules/vite/bin/vite.js','preview','--outDir',('"' + $frontendBuildPath + '"'),'--host','127.0.0.1','--port',"$FrontendPort",'--strictPort') $frontendPath $FrontendPort $frontendReady $frontendBuild

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
    Start-XinxinService 'gateway' $caddyExe @('run','--config',$caddyfilePath,'--adapter','caddyfile','--envfile',$gatewayEnvFile) $projectPath $GatewayPort $gatewayReady ((Get-XinxinFileHash $caddyfilePath) + ":$GatewayPort")
    $gatewayStarted=$true
  }catch{
    if(-not(Test-XinxinApplicationBlocked $_.Exception)){throw}
    Write-Host '[!] Windows 应用控制策略阻止了 Caddy；本机服务已就绪，桌面仍可使用。' -ForegroundColor Yellow
    Write-Host '    手机/局域网网关暂不可用；请由系统管理员核对 Caddy 的运行许可。未修改安全策略。'
  }finally{$env:XINXIN_LOG_DIR=$oldLogDir;$env:XINXIN_GATEWAY_PORT=$oldPort}
}

# 本机地址清单：供设置页与隧道脚本读取，不依赖任何外部服务
$addresses=@{
  local="http://127.0.0.1:$FrontendPort"
  lan=if($gatewayStarted -and $lanIp){"http://${lanIp}:$GatewayPort"}else{''}
  gateway_port=$GatewayPort
  updated=(Get-Date).ToString('s')
}
$addresses | ConvertTo-Json | ForEach-Object {
  [System.IO.File]::WriteAllText(
    (Join-Path $runtimePath 'addresses.json'),
    $_,
    (New-Object System.Text.UTF8Encoding($false))
  )
}

Write-Host ''
Write-Host 'Xinxin本地版 已启动'
Write-Host "  本机浏览器:    http://127.0.0.1:$FrontendPort"
if($gatewayStarted -and $lanIp){
  Write-Host "  手机/局域网:   http://${lanIp}:$GatewayPort   （同一 WiFi，无需服务器）"
}elseif($gatewayStarted){
  Write-Host "  手机/局域网:   http://<本机局域网IP>:$GatewayPort   （未能自动探测局域网 IP）"
}
Write-Host "  停止: ./Stop-Xinxin-Local.ps1"

# 防火墙自检：程序规则（放行 tools\caddy.exe）或端口规则任一存在即可。
# 早期只看端口规则，会把 Setup-Lan-Access 创建的程序规则误判为“未放行”。
if($gatewayStarted){
  $fwOk=$false
  $fwKind=''
  try{
    $programs=Get-NetFirewallRule -Direction Inbound -Enabled True -Action Allow -ErrorAction Stop |
      Where-Object { $_.DisplayName -like 'Caddy*' -or $_.DisplayName -like 'Xinxin*' }
    foreach($rule in $programs){
      $program=$rule | Get-NetFirewallApplicationFilter
      if($program.Program -and (Test-Path -LiteralPath $program.Program)){
        $appPath=[System.IO.Path]::GetFullPath($program.Program)
        $caddyPath=[System.IO.Path]::GetFullPath($caddyExe)
        if($appPath -eq $caddyPath){$fwOk=$true;$fwKind='程序规则';break}
      }
    }
    if(-not $fwOk){
      $portFilters=Get-NetFirewallPortFilter -Protocol TCP -ErrorAction Stop |
        Where-Object { $_.LocalPort -eq $GatewayPort -or $_.LocalPort -eq 'Any' }
      foreach($filter in $portFilters){
        $rule=$filter | Get-NetFirewallRule -ErrorAction SilentlyContinue
        if($rule -and $rule.Direction -eq 'Inbound' -and $rule.Enabled -eq 'True' -and $rule.Action -eq 'Allow'){
          $fwOk=$true;$fwKind='端口规则';break
        }
      }
    }
  }catch{$fwOk=$false}
  if($fwOk){
    Write-Host "  防火墙：已放行网关（$fwKind），手机与电脑在同一 WiFi 即可访问" -ForegroundColor DarkGray
  }else{
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
