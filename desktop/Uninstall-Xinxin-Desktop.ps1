#requires -Version 5.1
<#
.SYNOPSIS
  卸载 Xinxin电脑端：删除安装脚本创建的快捷方式（可选清理应用窗口的会话数据）
.DESCRIPTION
  只删除本安装器创建的东西：
    - 桌面快捷方式 Xinxin
    - 开始菜单 Xinxin本地版 文件夹
    - 开机自启快捷方式（如果注册过）
  不动项目代码、数据与正在运行的服务。

  用法：
    ./Uninstall-Xinxin-Desktop.ps1                    # 卸载快捷方式
    ./Uninstall-Xinxin-Desktop.ps1 -RemoveProfile     # 顺带清理应用窗口会话（重新登录）
    ./Uninstall-Xinxin-Desktop.ps1 -StopServices      # 卸载前先停止本机服务
#>
param(
  [switch]$RemoveProfile,
  [switch]$StopServices
)
$ErrorActionPreference = 'Stop'

$desktopPath = $PSScriptRoot
$projectPath = Split-Path -Path $desktopPath -Parent
$appProfile = Join-Path $projectPath '.runtime/desktop-profile'

$removed = 0
function Remove-XinxinShortcut([string]$LinkPath) {
  if (Test-Path -LiteralPath $LinkPath) {
    Remove-Item -LiteralPath $LinkPath -Force
    Write-Host "  已删除 $LinkPath"
    $script:removed += 1
  }
}

if ($StopServices) {
  $stopVbs = Join-Path $desktopPath 'Stop-Xinxin-Desktop.vbs'
  if (Test-Path -LiteralPath $stopVbs) {
    Write-Host '正在停止本机服务...'
    & (Join-Path $desktopPath 'Xinxin-Desktop.ps1') -Stop -Console
  }
}

# 1. 桌面
$desktopDir = [Environment]::GetFolderPath('Desktop')
if (-not $desktopDir) { $desktopDir = Join-Path $env:USERPROFILE 'Desktop' }
Remove-XinxinShortcut (Join-Path $desktopDir 'Xinxin.lnk')

# 2. 开始菜单（含可能残留的旧位置）
$startMenuRoot = [Environment]::GetFolderPath('StartMenu')
if (-not $startMenuRoot) { $startMenuRoot = (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu') }
$programsDir = Join-Path $startMenuRoot 'Programs\Xinxin本地版'
Remove-XinxinShortcut (Join-Path $programsDir 'Xinxin.lnk')
Remove-XinxinShortcut (Join-Path $programsDir '停止 Xinxin 服务.lnk')
if (Test-Path -LiteralPath $programsDir) {
  $leftovers = @(Get-ChildItem -LiteralPath $programsDir -Force -ErrorAction SilentlyContinue)
  if ($leftovers.Count -eq 0) {
    Remove-Item -LiteralPath $programsDir -Force
    Write-Host "  已删除空文件夹 $programsDir"
  } else {
    Write-Host "  [跳过] $programsDir 里还有其它内容，未删除文件夹" -ForegroundColor Yellow
  }
}

# 3. 开机自启
$startupDir = [Environment]::GetFolderPath('Startup')
if (-not $startupDir) { $startupDir = (Join-Path $startMenuRoot 'Programs\Startup') }
Remove-XinxinShortcut (Join-Path $startupDir 'Xinxin.lnk')

# 4. 应用窗口会话（Edge 独立配置目录：登录状态、窗口大小等）
if ($RemoveProfile) {
  if (Test-Path -LiteralPath $appProfile) {
    Remove-Item -LiteralPath $appProfile -Recurse -Force
    Write-Host "  已清理应用会话 $appProfile（下次启动需重新登录）"
  }
}

Write-Host ''
if ($removed -gt 0 -or $RemoveProfile) {
  Write-Host 'Xinxin 电脑端已卸载'
  Write-Host '  项目代码与数据未动；本机服务如需停止，请运行 Stop-Xinxin-Local.ps1'
} else {
  Write-Host '没有找到本安装器创建的快捷方式，无需卸载'
}
