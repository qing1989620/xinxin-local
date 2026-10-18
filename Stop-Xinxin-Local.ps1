# 停止 Xinxin本地版（只停止本启动器记录的后端、前端与局域网网关进程树，不动其它任何程序）
$ErrorActionPreference='Stop'
$manifestPath=Join-Path $PSScriptRoot '.runtime/processes.json'
if(-not(Test-Path -LiteralPath $manifestPath)){Write-Host 'No locally managed Xinxin processes.';exit 0}
$saved=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
foreach($entry in $saved.services){
  if($entry.role -notin @('frontend','backend','gateway')){continue}
  $instance=Get-Process -Id $entry.id -ErrorAction SilentlyContinue
  if($instance -and $instance.StartTime.ToUniversalTime().Ticks -eq [long]$entry.start_ticks){
    # A Windows venv launcher owns a child interpreter. Stop the verified tree.
    & (Join-Path $env:SystemRoot 'System32/taskkill.exe') /PID $instance.Id /T /F | Out-Null
    if($LASTEXITCODE -ne 0){throw "Could not stop the managed $($entry.role) process tree"}
    Write-Host "$($entry.role) stopped"
  }
}
@{services=@()} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
Write-Host 'Xinxin本地版 已全部停止；手机与局域网在服务停止期间将暂时无法连接。'
