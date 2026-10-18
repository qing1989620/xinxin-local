<#
.SYNOPSIS
  Xinxin本地版 · 局域网直连一次性配置向导
.DESCRIPTION
  把本机变成"同一 WiFi 下手机/电脑直接连"的私人 Agent 服务，无需域名、证书与公网 IP。
  本脚本完成：
    1. 探测本机局域网 IP 与建议网关端口，写入 .runtime/lan-access.json（git 已忽略）
    2. 检查/放行 Windows 防火墙入站规则（默认网关端口；需要管理员权限，非管理员时只给指引）
    3. 校验 Caddy 配置（PATH 里的 caddy 或 tools/caddy.exe 存在时）
    4. 打印手机连接地址与 APK 打包提示
  之后每次开机执行 Start-Xinxin-Local.ps1 即可。
.PARAMETER GatewayPort
  网关端口，默认 8080（与 Start-Xinxin-Local.ps1 -GatewayPort 保持一致）。
.EXAMPLE
  ./Setup-Lan-Access.ps1
.EXAMPLE
  ./Setup-Lan-Access.ps1 -GatewayPort 9090
#>
param(
  [int]$GatewayPort = 8080
)
$ErrorActionPreference='Stop'
$projectPath=$PSScriptRoot

# 防火墙入站规则需要管理员权限。非管理员时自动以管理员身份重启本脚本（会弹 UAC）。
$script:isAdmin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(-not $script:isAdmin){
  Write-Host '放行防火墙需要管理员权限，正在请求提权（请在 UAC 提示中点「是」）...' -ForegroundColor Yellow
  $argList="-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -GatewayPort $GatewayPort"
  try{
    Start-Process -FilePath powershell.exe -Verb RunAs -ArgumentList $argList | Out-Null
    Write-Host '已在新窗口以管理员身份重新运行本脚本，请在新窗口查看放行结果。' -ForegroundColor Green
  }catch{
    Write-Host "自动提权失败: $($_.Exception.Message)" -ForegroundColor DarkYellow
  }
  Read-Host '按回车关闭本窗口'
  exit
}

$runtimePath=Join-Path $projectPath '.runtime'
$toolsPath=Join-Path $projectPath 'tools'
$caddyfilePath=Join-Path $projectPath 'Caddyfile.local'
# 优先用 PATH 里的 caddy，其次用 tools/caddy.exe
$caddyOnPath=Get-Command caddy -ErrorAction SilentlyContinue
$caddyExe=if($caddyOnPath){$caddyOnPath.Source}else{Join-Path $toolsPath 'caddy.exe'}
$logsPath=Join-Path $projectPath 'logs'
$resultPath=Join-Path $runtimePath 'lan-access.json'
New-Item -ItemType Directory -Force -Path $runtimePath,$toolsPath,$logsPath | Out-Null

function Write-Step([string]$Text){Write-Host '';Write-Host "==> $Text" -ForegroundColor Cyan}

# ---------- 1. 局域网 IP ----------
Write-Step '探测本机局域网 IP'
$lanIp=''
$adapters=@()
try{
  $cfg=Get-NetIPConfiguration | Where-Object {$_.IPv4DefaultGateway -ne $null -and $_.NetAdapter.Status -eq 'Up'}
  foreach($item in $cfg){
    if($item.IPv4Address){$adapters+=[pscustomobject]@{Name=$item.NetAdapter.Name;Ip=$item.IPv4Address.IPAddress}}
  }
}catch{}
if($adapters){
  $lanIp=($adapters | Select-Object -First 1).Ip
  Write-Host "活动网卡: $($adapters.Name -join ', ')"
  Write-Host "局域网 IP: $lanIp"
}else{
  Write-Host '未能自动探测到带默认网关的 IPv4 网卡（可能只有 WiFi 未连接或使用了静态配置）。'
}
$lanOrigin=if($lanIp){"http://${lanIp}:$GatewayPort"}else{"http://<本机局域网IP>:$GatewayPort"}

# ---------- 2. 防火墙 ----------
Write-Step '检查 Windows 防火墙入站规则'
$ruleName="Xinxin本地版网关 (TCP $GatewayPort)"

# 网络位置是「公用」时，Windows 会拦截入站连接，必须先切到「专用」
try{
  $profile=Get-NetConnectionProfile -ErrorAction Stop |
    Where-Object { $_.IPv4Connectivity -ne 'None' } | Select-Object -First 1
  if($profile){
    if($profile.NetworkCategory -eq 'Public'){
      Write-Host "网络位置: 公用（$($profile.Name)）——公用网络下 Windows 会拦截入站连接" -ForegroundColor DarkYellow
      Write-Host '  以管理员身份执行下面这行，把当前网络改为专用：' -ForegroundColor DarkYellow
      Write-Host "     Set-NetConnectionProfile -InterfaceAlias '$($profile.InterfaceAlias)' -NetworkCategory Private"
    }else{
      Write-Host "网络位置: 专用（$($profile.Name)）"
    }
  }
}catch{}
$existingRule=Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if($existingRule){
  Write-Host "已存在放行规则: $ruleName"
}else{
  $isAdmin=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if($isAdmin){
    try{
      New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $GatewayPort -Action Allow -Profile Any | Out-Null
      Write-Host "已放行 TCP $GatewayPort 入站（仅局域网可达；公网暴露请勿把该端口做路由器转发）" -ForegroundColor Green
    }catch{
      Write-Host "自动放行失败: $($_.Exception.Message)" -ForegroundColor DarkYellow
      Write-Host "可手动执行: New-NetFirewallRule -DisplayName '$ruleName' -Direction Inbound -Protocol TCP -LocalPort $GatewayPort -Action Allow"
    }
  }else{
    Write-Host '当前不是管理员权限，跳过自动放行。'
    Write-Host '  → 关闭本窗口，右键 PowerShell 选「以管理员身份运行」，再执行本脚本。'
    Write-Host "  → 或直接在管理员窗口粘贴下面这行命令："
    Write-Host "     New-NetFirewallRule -DisplayName '$ruleName' -Direction Inbound -Protocol TCP -LocalPort $GatewayPort -Action Allow -Profile Any"
  }
}

# ---------- 3. Caddy ----------
Write-Step '检查 Caddy 网关'
if(Test-Path -LiteralPath $caddyExe){
  $version=& $caddyExe version
  Write-Host "Caddy 版本: $version"
  $oldEap=$ErrorActionPreference
  $ErrorActionPreference='Continue'
  try{
    $validateOut=& $caddyExe validate --config $caddyfilePath --adapter caddyfile 2>&1
    $validateExit=$LASTEXITCODE
  }finally{$ErrorActionPreference=$oldEap}
  $validateText=($validateOut | Out-String)
  if($validateExit -ne 0 -or $validateText -notmatch 'Valid configuration'){
    Write-Host $validateText -ForegroundColor DarkYellow
    throw "Caddy 配置校验失败（exit=$validateExit），请检查上面的错误信息"
  }
  Write-Host 'Caddy 配置有效'
}elsif(-not $caddyOnPath){
  Write-Host '未找到 caddy（PATH 与 tools/caddy.exe 均无）'
  Write-Host '  局域网直连依赖 Caddy 做单端口入口。安装方式：'
  Write-Host '    winget install Caddy.Caddy'
  Write-Host '  或从 https://caddyserver.com/download 下载 Windows amd64 标准版（无需任何插件）放到 tools/caddy.exe'
  Write-Host '  仅本机调试可加 -NoGateway 跳过网关。'
}

# ---------- 4. 记录结果 ----------
@{lan_ip=$lanIp;gateway_port=$GatewayPort;lan_origin=$lanOrigin;updated_at=(Get-Date).ToString('s')} |
  ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding UTF8
Write-Host ''
Write-Host "已记录: $resultPath（git 已忽略）"

# ---------- 5. 使用指引 ----------
Write-Step '接下来你要做的事'
Write-Host "1) 启动服务:"
Write-Host "     .\Start-Xinxin-Local.ps1$(if($GatewayPort -ne 8080){" -GatewayPort $GatewayPort"})"
Write-Host "2) 手机连同一个 WiFi 后，浏览器或 APK 访问:"
Write-Host "     $lanOrigin"
Write-Host "3) 手机 APK（可选，把局域网地址预填进安装包）:"
Write-Host "     frontend\build-android.ps1 -Local -Release -BackendUrl $lanOrigin"
Write-Host "     （APK 里也可以随时在设置页改服务器地址；局域网 IP 变化后以新地址为准）"
Write-Host ''
Write-Host "说明：本方案只覆盖同一局域网。手机在外网时无法连家里电脑，除非另行配置端口映射或内网穿透。" -ForegroundColor DarkYellow
Write-Host "完成。服务运行后，同一 WiFi 下的手机/电脑访问 $lanOrigin 即可使用（数据只在本机 backend/data）。" -ForegroundColor Green
