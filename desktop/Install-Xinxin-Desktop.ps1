#requires -Version 5.1
<#
.SYNOPSIS
  安装 Xinxin电脑端：创建桌面与开始菜单快捷方式（可选开机自启）
.DESCRIPTION
  不复制、不构建任何东西，只创建指向 desktop\Xinxin-Desktop.vbs 的快捷方式：
    - 桌面：Xinxin
    - 开始菜单：Xinxin本地版\Xinxin、Xinxin本地版\停止 Xinxin 服务
    - 可选（-AutoStart）：开机自启（登录后自动启动电脑端）

  用法：
    ./Install-Xinxin-Desktop.ps1                # 安装（桌面 + 开始菜单）
    ./Install-Xinxin-Desktop.ps1 -AutoStart     # 顺带注册开机自启
    ./Install-Xinxin-Desktop.ps1 -Start         # 装完立即启动一次
#>
param(
  [switch]$AutoStart,
  [switch]$Start
)
$ErrorActionPreference = 'Stop'

$desktopPath = $PSScriptRoot
$projectPath = Split-Path -Path $desktopPath -Parent
$launcherVbs = Join-Path $desktopPath 'Xinxin-Desktop.vbs'
$stopVbs = Join-Path $desktopPath 'Stop-Xinxin-Desktop.vbs'
$iconFile = Join-Path $desktopPath 'assets/xinxin.ico'

foreach ($required in @($launcherVbs, $stopVbs)) {
  if (-not (Test-Path -LiteralPath $required)) {
    throw "缺少文件：$required（请保持 desktop 目录完整）"
  }
}
if (-not (Test-Path -LiteralPath $iconFile)) {
  Write-Host "[!] 未找到图标 assets/xinxin.ico，快捷方式将使用默认图标" -ForegroundColor Yellow
}

$shell = New-Object -ComObject 'WScript.Shell'
$wscript = Join-Path $env:SystemRoot 'System32\wscript.exe'

function New-XinxinShortcut([string]$LinkPath, [string]$VbsPath, [string]$Description) {
  $directory = Split-Path -Path $LinkPath -Parent
  if (-not (Test-Path -LiteralPath $directory)) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
  }
  $shortcut = $shell.CreateShortcut($LinkPath)
  $shortcut.TargetPath = $wscript
  $shortcut.Arguments = '"' + $VbsPath + '"'
  $shortcut.WorkingDirectory = $desktopPath
  if (Test-Path -LiteralPath $iconFile) {
    $shortcut.IconLocation = $iconFile + ',0'
  }
  $shortcut.Description = $Description
  $shortcut.Save()
  Write-Host "  已创建 $LinkPath"
}

# 1. 桌面快捷方式（自动兼容 OneDrive 重定向的桌面）
$desktopDir = [Environment]::GetFolderPath('Desktop')
if (-not $desktopDir) { $desktopDir = Join-Path $env:USERPROFILE 'Desktop' }
New-XinxinShortcut (Join-Path $desktopDir 'Xinxin.lnk') $launcherVbs 'Xinxin本地版 · 电脑软件端'

# 2. 开始菜单（程序文件夹）
$startMenuRoot = [Environment]::GetFolderPath('StartMenu')
if (-not $startMenuRoot) { $startMenuRoot = (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu') }
$programsDir = Join-Path $startMenuRoot 'Programs\Xinxin本地版'
New-XinxinShortcut (Join-Path $programsDir 'Xinxin.lnk') $launcherVbs 'Xinxin本地版 · 电脑软件端'
New-XinxinShortcut (Join-Path $programsDir '停止 Xinxin 服务.lnk') $stopVbs '停止 Xinxin 本机服务（手机与网页同时停止）'

# 3. 开机自启（写入启动文件夹，随时可删）
if ($AutoStart) {
  $startupDir = [Environment]::GetFolderPath('Startup')
  if (-not $startupDir) { $startupDir = (Join-Path $startMenuRoot 'Programs\Startup') }
  New-XinxinShortcut (Join-Path $startupDir 'Xinxin.lnk') $launcherVbs 'Xinxin本地版 · 电脑软件端（开机自启）'
  Write-Host '  已注册开机自启（启动文件夹，删除该快捷方式即可取消）'
}

# 4. Edge 自检：电脑端的应用窗口由 Edge 承载，缺失时退回系统默认浏览器
$edgeFound = $false
foreach ($candidate in @(
  (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'),
  (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe')
)) {
  if ($candidate -and (Test-Path -LiteralPath $candidate)) { $edgeFound = $true; break }
}
if (-not $edgeFound) {
  Write-Host '[!] 未检测到 Microsoft Edge：电脑端会自动改用系统默认浏览器打开，功能不受影响' -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'Xinxin 电脑端安装完成'
Write-Host '  双击桌面上的 Xinxin 图标即可使用；首次启动会自动拉起本机服务'
Write-Host '  卸载：运行 ./Uninstall-Xinxin-Desktop.ps1（或双击 卸载电脑端.cmd）'
Write-Host "  说明文档：docs/电脑端.md"

if ($Start) {
  Write-Host ''
  Write-Host '正在启动电脑端...'
  & (Join-Path $desktopPath 'Xinxin-Desktop.ps1') -Console
}
