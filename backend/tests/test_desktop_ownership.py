"""Process ancestry identity checks in a mock-only PowerShell process."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(os.name != "nt" or not shutil.which("powershell.exe"), reason="Windows process identity")
def test_managed_port_rejects_reused_parent_pids_and_cycles(tmp_path):
    helper = Path(__file__).resolve().parents[2] / "desktop/Local-ServiceState.ps1"
    script = tmp_path / "ownership.ps1"
    script.write_text('''param([string]$Helpers)
$ErrorActionPreference='Stop'
. $Helpers
$script:processTimes=@{10=[datetime]'2026-10-21T01:00:00';20=[datetime]'2026-10-21T01:10:00';30=[datetime]'2026-10-21T01:05:00'}
$script:parents=@{30=20;20=10;10=0}
function Get-Process {param([int]$Id,[string]$ErrorAction) if($script:processTimes.ContainsKey($Id)){[pscustomobject]@{StartTime=$script:processTimes[$Id]}}}
function Get-NetTCPConnection {param([int]$LocalPort,[string]$State,[string]$ErrorAction) [pscustomobject]@{OwningProcess=30}}
function Get-CimInstance {param([string]$ClassName,[string]$Filter,[string]$ErrorAction) $ident=[int]($Filter -replace '[^0-9]','');[pscustomobject]@{ParentProcessId=$script:parents[$ident]}}
if(Test-XinxinManagedPort 10 12345){throw 'Reused parent PID was accepted'}
$script:processTimes[20]=[datetime]'2026-10-21T01:03:00'
if(-not(Test-XinxinManagedPort 10 12345)){throw 'Real child process was rejected'}
$script:processTimes[20]=[datetime]'2026-10-21T01:05:00'
$script:parents[20]=30
if(Test-XinxinManagedPort 10 12345){throw 'Cycle was accepted'}
$script:parents[20]=0
if(Test-XinxinManagedPort 10 12345){throw 'Unrelated listener was accepted'}
$script:processTimes.Remove(10)
if(Test-XinxinManagedPort 10 12345){throw 'Missing root was accepted'}
Write-Output 'ownership checks passed'
''', encoding="utf-8-sig")
    result = subprocess.run([shutil.which("powershell.exe"), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-Helpers", str(helper)], capture_output=True, timeout=20)
    assert result.returncode == 0, result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace")
    assert b"ownership checks passed" in result.stdout


@pytest.mark.skipif(os.name != "nt" or not shutil.which("powershell.exe"), reason="Windows application control")
def test_only_application_control_error_allows_optional_gateway_degradation(tmp_path):
    helper = Path(__file__).resolve().parents[2] / "desktop/Local-ServiceState.ps1"
    script = tmp_path / "policy.ps1"
    script.write_text('''param([string]$Helpers)
$ErrorActionPreference='Stop'
. $Helpers
$blocked=New-Object System.ComponentModel.Win32Exception(4551)
if(-not(Test-XinxinApplicationBlocked $blocked)){throw 'Blocked gateway was not recognized'}
$wrapped=New-Object System.InvalidOperationException('wrapper',$blocked)
if(-not(Test-XinxinApplicationBlocked $wrapped)){throw 'Wrapped application control failure was not recognized'}
$legacy=New-Object System.InvalidOperationException('This command cannot be run due to the error: An Application Control policy has blocked this file.')
if(-not(Test-XinxinApplicationBlocked $legacy)){throw 'PowerShell 5.1 flattened application control failure was not recognized'}
$denied=New-Object System.ComponentModel.Win32Exception(5)
if(Test-XinxinApplicationBlocked $denied){throw 'Unrelated access error was hidden'}
if(Test-XinxinApplicationBlocked (New-Object System.Exception('Bad gateway configuration'))){throw 'Configuration error was hidden'}
if(Test-XinxinApplicationBlocked (New-Object System.InvalidOperationException('This command cannot be run due to the error: Access is denied.'))){throw 'Generic launch failure was hidden'}
''', encoding="utf-8-sig")
    result = subprocess.run([shutil.which("powershell.exe"), "-NoProfile", "-File", str(script), str(helper)], capture_output=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(os.name != "nt" or not shutil.which("powershell.exe"), reason="Windows application control")
def test_localized_application_control_errors_preserve_loopback_startup(tmp_path):
    helper = Path(__file__).resolve().parents[2] / "desktop/Local-ServiceState.ps1"
    script = tmp_path / "localized-policy.ps1"
    script.write_text('''param([string]$Helpers)
$ErrorActionPreference='Stop'
. $Helpers
# Explorer and the test runner can have different UI languages. Start-Process
# localizes its wrapper independently from the native Windows error text.
$prefixes=@('This command cannot be run due to the error: ','由于出现以下错误，无法运行此命令: ')
$endings=@('.','。')
$nativeMessages=@('An Application Control policy has blocked this file','应用程序控制策略已阻止此文件。')
for($i=0;$i -lt $prefixes.Count;$i++){
  foreach($nativeMessage in $nativeMessages){
    $message=$prefixes[$i]+$nativeMessage+$endings[$i]
    $failure=New-Object System.InvalidOperationException($message)
    if(-not(Test-XinxinApplicationBlocked $failure)){throw "Localized policy failure escaped: $message"}
    $wrapped=New-Object System.Exception('outer wrapper',$failure)
    if(-not(Test-XinxinApplicationBlocked $wrapped)){throw 'Nested localized policy failure escaped'}
    if(Test-XinxinApplicationBlocked (New-Object System.Exception($message))){throw 'Unrelated exception was hidden'}
    if(Test-XinxinApplicationBlocked (New-Object System.InvalidOperationException('Configuration failed: '+$message))){throw 'Unrelated configuration error was hidden'}
  }
}
foreach($code in @(2,5,577)){
  if(Test-XinxinApplicationBlocked (New-Object System.ComponentModel.Win32Exception($code))){throw "Unrelated native error $code was hidden"}
}
foreach($message in @('由于出现以下错误，无法运行此命令: 拒绝访问。','由于出现以下错误，无法运行此命令: 系统找不到指定的文件。','Bad gateway configuration')){
  if(Test-XinxinApplicationBlocked (New-Object System.InvalidOperationException($message))){throw 'Unrelated localized launch failure was hidden'}
}
''', encoding="utf-8-sig")
    result = subprocess.run([shutil.which("powershell.exe"), "-NoProfile", "-File", str(script), str(helper)], capture_output=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
