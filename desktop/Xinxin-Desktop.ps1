#requires -Version 5.1
<#
.SYNOPSIS
  Xinxin本地版 · 电脑软件端启动器
.DESCRIPTION
  让 Xinxin 像普通桌面软件一样被使用：双击图标 → 自动就绪 → 打开独立应用窗口。

  设计约束（与本地版整体一致）：
  - 不新增任何服务器：电脑端复用本机已有的后端 / 前端 / 网关（手机、网页共用的同一套服务）
  - 不改手机端与网页端：本脚本只负责「确保服务就绪 + 打开一个应用窗口」
  - 服务没起时自动拉起（等价于 Start-Xinxin-Local.ps1 -NoBrowser），期间显示启动页
  - 独立 Edge 应用窗口：无地址栏、无标签页，独立配置目录，不污染日常浏览器
  - 单实例：窗口已开着就激活它，不重复开窗
  - 关闭窗口不等于停止服务：手机端、网页端继续可用；停止请用「停止 Xinxin 服务」快捷方式

  用法：
    Xinxin-Desktop.ps1                 # 正常启动（由快捷方式经 VBS 无窗口调用）
    Xinxin-Desktop.ps1 -Console        # 前台运行并打印日志（排查用）
    Xinxin-Desktop.ps1 -Stop           # 关闭应用窗口并停止本机服务
    Xinxin-Desktop.ps1 -Width 1600 -Height 1000
    Xinxin-Desktop.ps1 -DebugPort 9339 # 给应用窗口开 CDP 调试端口（自动化验收用）
#>
param(
  [switch]$Console,
  [switch]$Stop,
  [int]$Width = 1366,
  [int]$Height = 860,
  [int]$DebugPort = 0
)
$ErrorActionPreference = 'Stop'

$desktopPath = $PSScriptRoot
$projectPath = Split-Path -Path $desktopPath -Parent
$runtimePath = Join-Path $projectPath '.runtime'
$assetsPath = Join-Path $desktopPath 'assets'
$logPath = Join-Path $runtimePath 'desktop.log'
$lockPath = Join-Path $runtimePath 'desktop-launcher.lock'
$appProfile = Join-Path $runtimePath 'desktop-profile'
$splashProfile = Join-Path $runtimePath 'desktop-splash-profile'
$appTitle = 'Xinxin本地版'
$splashTitle = 'Xinxin 正在启动'
. (Join-Path $desktopPath 'Local-ServiceState.ps1')

function Write-Log([string]$Message) {
  $line = '[' + (Get-Date).ToString('yyyy-MM-dd HH:mm:ss') + '] ' + $Message
  try {
    New-Item -ItemType Directory -Force -Path $runtimePath | Out-Null
    Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
  } catch {}
  if ($Console) { Write-Host $line }
}

function Trim-Log {
  # 单文件超过 256KB 只保留尾部，防止长期自启把磁盘写满
  try {
    $item = Get-Item -LiteralPath $logPath -ErrorAction Stop
    if ($item.Length -gt 262144) {
      $tail = Get-Content -LiteralPath $logPath -Tail 150
      [System.IO.File]::WriteAllLines($logPath, $tail, (New-Object System.Text.UTF8Encoding($false)))
    }
  } catch {}
}

function Restore-ProxyEnvironment {
  # Windows PowerShell 的 Start-Process 在大小写重复的代理变量（HTTP_PROXY 与 http_proxy 并存）时报错；
  # 与 Start-Xinxin-Local.ps1 同一处置：仅当大写变量也存在时收起小写变体，不动其它环境。
  foreach ($name in 'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy') {
    $upper = $name.ToUpperInvariant()
    $lowerValue = [Environment]::GetEnvironmentVariable($name, 'Process')
    if ($null -ne $lowerValue -and $null -ne [Environment]::GetEnvironmentVariable($upper, 'Process')) {
      [Environment]::SetEnvironmentVariable($name, $null, 'Process')
      Write-Log "normalized duplicate proxy variable: $name"
    }
  }
}

function Get-EnvValue([string]$Key, [string]$Default) {
  $envFile = Join-Path $projectPath 'backend/.env'
  if (Test-Path -LiteralPath $envFile) {
    try {
      $found = Select-String -LiteralPath $envFile -Pattern "(?m)^\s*$Key=(\d+)" | Select-Object -First 1
      if ($found) { return [int]$found.Matches[0].Groups[1].Value }
    } catch {}
  }
  return $Default
}

function Get-GatewayPort {
  # 网关端口由 Start-Xinxin-Local.ps1 写入 .runtime/gateway.env（用户可能自定义过）
  $envFile = Join-Path $runtimePath 'gateway.env'
  if (Test-Path -LiteralPath $envFile) {
    try {
      $found = Select-String -LiteralPath $envFile -Pattern '(?m)^\s*XINXIN_GATEWAY_PORT=(\d+)' | Select-Object -First 1
      if ($found) { return [int]$found.Matches[0].Groups[1].Value }
    } catch {}
  }
  return 8080
}

function Test-ServiceHealthy([int]$Port) {
  # 直连 127.0.0.1 并禁用代理：本机探测绝不该走任何代理
  try {
    $request = [System.Net.WebRequest]::Create("http://127.0.0.1:$Port/health")
    $request.Proxy = $null
    $request.Timeout = 3000
    $response = $request.GetResponse()
    $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
    $body = $reader.ReadToEnd()
    $reader.Close()
    $response.Close()
    return ($body -match '"status"\s*:\s*"ok"')
  } catch {
    return $false
  }
}

function Get-EdgePath {
  $candidates = @()
  if ($env:ProgramFiles) { $candidates += (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe') }
  if (${env:ProgramFiles(x86)}) { $candidates += (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe') }
  foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path -LiteralPath $candidate)) { return $candidate }
  }
  try {
    $reg = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe' -ErrorAction Stop
    $default = $reg.'(default)'
    if ($default -and (Test-Path -LiteralPath $default)) { return $default }
  } catch {}
  $onPath = Get-Command msedge -ErrorAction SilentlyContinue
  if ($onPath) { return $onPath.Source }
  return ''
}

function Get-EdgeAppWindows([string]$Profile) {
  # 只认「指定配置目录 + --app」的 Edge 主进程，避免误伤用户的日常浏览器窗口
  $needle = $Profile.ToLowerInvariant()
  try {
    $processes = @(Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" -ErrorAction Stop)
  } catch {
    try {
      $processes = @(Get-WmiObject Win32_Process -Filter "Name='msedge.exe'" -ErrorAction Stop)
    } catch {
      return @()
    }
  }
  $found = @()
  foreach ($process in $processes) {
    $commandLine = [string]$process.CommandLine
    if ($commandLine -and $commandLine.ToLowerInvariant().Contains($needle) -and $commandLine.Contains('--app=')) {
      $found += $process
    }
  }
  return $found
}

function Stop-WindowTree([int]$ProcessId) {
  $taskkill = Join-Path $env:SystemRoot 'System32\taskkill.exe'
  & $taskkill /PID $ProcessId /T /F | Out-Null
}

function Show-WindowByTitle([string]$Title) {
  try {
    $shell = New-Object -ComObject 'WScript.Shell'
    return [bool]$shell.AppActivate($Title)
  } catch {
    return $false
  }
}

function Open-AppWindow([string]$Url, [string]$Profile, [int]$WindowWidth, [int]$WindowHeight) {
  $edge = Get-EdgePath
  if (-not $edge) {
    # 没有 Edge 也不阻断使用：退回系统默认浏览器打开同一个本地地址
    Start-Process $Url | Out-Null
    Write-Log "Edge not found; opened the default browser instead: $Url"
    return $null
  }
  $arguments = @(
    "--app=$Url",
    "--user-data-dir=$Profile",
    "--window-size=$WindowWidth,$WindowHeight",
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-sync'
  )
  if ($DebugPort -gt 0) { $arguments += "--remote-debugging-port=$DebugPort" }
  $process = Start-Process -FilePath $edge -ArgumentList $arguments -WorkingDirectory $desktopPath -PassThru
  Write-Log "opened window: $Url (pid $($process.Id))"
  return $process
}

function Protect-Html([string]$Text) {
  if ($null -eq $Text) { return '' }
  return $Text.Replace('&', '&amp;').Replace('<', '&lt;').Replace('>', '&gt;').Replace('"', '&quot;')
}

function Add-DesktopFlag([string]$Url) {
  # 告诉前端"这是电脑端窗口"：隐藏安装/离线就绪提示。网页与手机端不带这个参数，行为不变。
  return $Url.TrimEnd('/') + '/?desktop=1'
}

function Reset-StaleWebCache([string]$Profile) {
  # 前端重新构建后，旧的 Service Worker 会把旧界面一直留在窗口里（整包离线缓存）。
  # 开窗前按 dist/index.html 的哈希比对一次，变了就清掉这个独立配置目录的离线缓存。
  # 只在没有窗口运行时调用，避免删掉正在使用的缓存。
  $indexPath = Join-Path $projectPath 'frontend\dist\index.html'
  if (-not (Test-Path -LiteralPath $indexPath)) { return }
  $stamp = ''
  try {
    $stamp = Get-XinxinFileHash $indexPath
  } catch {
    return
  }
  $stampPath = Join-Path $Profile 'build-stamp.txt'
  $previous = ''
  if (Test-Path -LiteralPath $stampPath) {
    $saved = Get-Content -LiteralPath $stampPath -Raw -ErrorAction SilentlyContinue
    if ($null -ne $saved) { $previous = $saved.Trim() }
  }
  if ($previous -eq $stamp) { return }
  foreach ($name in @('Service Worker', 'Cache', 'Code Cache')) {
    $target = Join-Path $Profile ('Default\' + $name)
    $profileRoot = [System.IO.Path]::GetFullPath($Profile).TrimEnd('\') + '\'
    $target = [System.IO.Path]::GetFullPath($target)
    if (-not $target.StartsWith($profileRoot, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid desktop cache path' }
    if (Test-Path -LiteralPath $target) {
      Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue
      Write-Log ('cleared stale ' + $name + ' (new frontend build)')
    }
  }
  try {
    Set-Content -LiteralPath $stampPath -Value $stamp -Encoding ASCII
  } catch {
  }
  Write-Log 'offline cache reset for the new frontend build'
}

function Show-ErrorWindow([string]$Message) {
  $templatePath = Join-Path $assetsPath 'error-template.html'
  if (-not (Test-Path -LiteralPath $templatePath)) { return }
  $lines = @()
  if (Test-Path -LiteralPath $logPath) {
    foreach ($line in (Get-Content -LiteralPath $logPath -Encoding UTF8 -Tail 14 -ErrorAction SilentlyContinue)) {
      $lines += (Protect-Html $line)
    }
  }
  $html = Get-Content -LiteralPath $templatePath -Encoding UTF8 -Raw
  $html = $html.Replace('{{MESSAGE}}', (Protect-Html $Message))
  $html = $html.Replace('{{LOG}}', ($lines -join '<br/>'))
  # 让用户知道完整日志在哪：错误页只放尾部，排查时常常需要全文
  $html = $html.Replace('{{LOGPATH}}', (Protect-Html $logPath))
  $outPath = Join-Path $runtimePath 'desktop-error.html'
  [System.IO.File]::WriteAllText($outPath, $html, (New-Object System.Text.UTF8Encoding($false)))
  $edge = Get-EdgePath
  if (-not $edge) { return }
  $url = 'file:///' + $outPath.Replace('\', '/')
  Start-Process -FilePath $edge -ArgumentList @(
    "--app=$url",
    "--user-data-dir=$splashProfile",
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-sync',
    '--window-size=680,760'
  ) -WorkingDirectory $desktopPath | Out-Null
  Write-Log "opened the error window: $url"
}

function Start-LocalStack {
  $startScript = Join-Path $projectPath 'Start-Xinxin-Local.ps1'
  if (-not (Test-Path -LiteralPath $startScript)) { throw "找不到启动脚本：$startScript" }
  Write-Log 'local stack is down; starting it now (same as Start-Xinxin-Local.ps1 -NoBrowser)'
  # 子脚本输出单独落盘再按行搬进日志：PowerShell 的 *>> 重定向写的是 UTF-16，
  # 直接混进 UTF-8 日志会出现乱码行。捕获文件每次先删掉——*>> 是追加写，
  # 不清空会把上一次启动的输出重复搬进日志。
  $startLog = Join-Path $runtimePath 'desktop-start.log'
  if (Test-Path -LiteralPath $startLog) { Remove-Item -LiteralPath $startLog -Force -ErrorAction SilentlyContinue }
  try {
    & $startScript -NoBrowser *>> $startLog
  } finally {
    if (Test-Path -LiteralPath $startLog) {
      foreach ($line in (Get-Content -LiteralPath $startLog -Encoding Unicode -ErrorAction SilentlyContinue)) {
        if ($line -and $line.Trim()) { Write-Log "  start| $($line.TrimEnd())" }
      }
    }
  }
}

$script:lockStream = $null
function Take-LauncherLock {
  # 原子创建锁文件：启动阶段同一时间只允许一个启动器，避免重复拉起服务、重复开启动页
  for ($attempt = 0; $attempt -lt 2; $attempt++) {
    try {
      $stream = [System.IO.File]::Open($lockPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
      $bytes = [System.Text.Encoding]::UTF8.GetBytes("$PID")
      $stream.Write($bytes, 0, $bytes.Length)
      $stream.Flush()
      $script:lockStream = $stream
      return $true
    } catch {
      $owner = 0
      try { $owner = [int](Get-Content -LiteralPath $lockPath -Raw -ErrorAction Stop) } catch {}
      if ($owner -gt 0 -and (Get-Process -Id $owner -ErrorAction SilentlyContinue)) {
        return $false
      }
      # 上一次启动器已被强行结束，留下失效锁：清掉重试一次
      Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue
    }
  }
  return $false
}

function Release-LauncherLock {
  try {
    if ($script:lockStream) { $script:lockStream.Close(); $script:lockStream = $null }
  } catch {}
  try { Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue } catch {}
}

# ---------------------------------------------------------------- 入口
New-Item -ItemType Directory -Force -Path $runtimePath | Out-Null
Trim-Log
Write-Log "desktop session start (pid $PID, console=$Console, stop=$Stop)"

if ($Stop) {
  # 关闭可能开着的应用窗口与启动页，再停止本机服务（手机/网页随服务一起停止，这是显式停止）
  foreach ($profile in @($appProfile, $splashProfile)) {
    foreach ($window in @(Get-EdgeAppWindows $profile)) {
      try {
        Stop-WindowTree $window.ProcessId
        Write-Log "closed window pid $($window.ProcessId)"
      } catch {
        Write-Log "could not close window pid $($window.ProcessId): $($_.Exception.Message)"
      }
    }
  }
  $stopScript = Join-Path $projectPath 'Stop-Xinxin-Local.ps1'
  if (Test-Path -LiteralPath $stopScript) {
    # 与启动同理：输出先落盘再按行搬进日志，避免 UTF-16 重定向污染；同理先清空
    $stopLog = Join-Path $runtimePath 'desktop-stop.log'
    try {
      if (Test-Path -LiteralPath $stopLog) { Remove-Item -LiteralPath $stopLog -Force -ErrorAction SilentlyContinue }
      & $stopScript *>> $stopLog
      if (Test-Path -LiteralPath $stopLog) {
        foreach ($line in (Get-Content -LiteralPath $stopLog -ErrorAction SilentlyContinue)) {
          if ($line -and $line.Trim()) { Write-Log "  stop| $($line.TrimEnd())" }
        }
      }
    } catch {
      Write-Log "stop failed: $($_.Exception.Message)"
    }
  }
  Write-Log 'stop finished'
  exit 0
}

Restore-ProxyEnvironment

$gatewayPort = Get-GatewayPort
$frontendPort = Get-EnvValue 'XINXIN_FRONTEND_PORT' '5180'
Write-Log "ports: gateway=$gatewayPort frontend=$frontendPort"

$entryUrl = ''
if (Test-ServiceHealthy $gatewayPort) {
  $entryUrl = "http://127.0.0.1:$gatewayPort"
} elseif (Test-ServiceHealthy $frontendPort) {
  $entryUrl = "http://127.0.0.1:$frontendPort"
}

# 每次先核对本地栈版本：健康但过期的后端也必须更新。
if (-not (Take-LauncherLock)) {
  if (-not (Show-WindowByTitle $appTitle)) { Show-WindowByTitle $splashTitle | Out-Null }
  Write-Log 'another launcher is already starting the stack; nothing to do'
  exit 0
}

$splash = $null
try {
  $splashFile = Join-Path $assetsPath 'starting.html'
  if (-not $entryUrl -and (Test-Path -LiteralPath $splashFile) -and (Get-EdgePath)) {
    $splash = Open-AppWindow ('file:///' + $splashFile.Replace('\', '/')) $splashProfile 520 600
  }

  Start-LocalStack

  $deadline = (Get-Date).AddSeconds(60)
  while ((Get-Date) -lt $deadline) {
    if (Test-ServiceHealthy $gatewayPort) { $entryUrl = "http://127.0.0.1:$gatewayPort"; break }
    if (Test-ServiceHealthy $frontendPort) { $entryUrl = "http://127.0.0.1:$frontendPort"; break }
    Start-Sleep -Milliseconds 500
  }
  if (-not $entryUrl) { throw '本地服务未在预期时间内就绪，详见 .runtime/desktop.log' }

  # A previous failed launch may have left an error window in this dedicated
  # temporary profile. Once healthy, close those windows before reusing the app.
  foreach ($temporary in @(Get-EdgeAppWindows $splashProfile)) {
    try { Stop-WindowTree $temporary.ProcessId; Write-Log 'closed temporary startup window' } catch {}
  }
  $splash = $null

  $open = @(Get-EdgeAppWindows $appProfile)
  if ($open.Count -gt 0 -and (Test-XinxinDesktopBuild $projectPath $appProfile)) {
    Show-WindowByTitle $appTitle | Out-Null
    Write-Log 'verified current services and activated the running app window'
    if ($splash -and -not $splash.HasExited) { try { Stop-WindowTree $splash.Id } catch {} }
    exit 0
  }

  # 启动前若留着上次的窗口，它已经是一张死页面：关掉重开
  foreach ($stale in @(Get-EdgeAppWindows $appProfile)) {
    try {
      Stop-WindowTree $stale.ProcessId
      Write-Log "closed stale window pid $($stale.ProcessId)"
    } catch {
      Write-Log "could not close stale window: $($_.Exception.Message)"
    }
  }

  if ($splash -and -not $splash.HasExited) {
    try { Stop-WindowTree $splash.Id } catch {}
  }
  Reset-StaleWebCache $appProfile
  Open-AppWindow (Add-DesktopFlag $entryUrl) $appProfile $Width $Height | Out-Null
  exit 0
} catch {
  Write-Log "startup failed: $($_.Exception.Message)"
  if ($splash -and -not $splash.HasExited) {
    try { Stop-WindowTree $splash.Id } catch {}
  }
  Show-ErrorWindow $_.Exception.Message
  exit 1
} finally {
  Release-LauncherLock
}
