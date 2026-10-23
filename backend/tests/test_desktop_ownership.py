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
$denied=New-Object System.ComponentModel.Win32Exception(5)
if(Test-XinxinApplicationBlocked $denied){throw 'Unrelated access error was hidden'}
if(Test-XinxinApplicationBlocked (New-Object System.Exception('Bad gateway configuration'))){throw 'Configuration error was hidden'}
''', encoding="utf-8-sig")
    result = subprocess.run([shutil.which("powershell.exe"), "-NoProfile", "-File", str(script), str(helper)], capture_output=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
