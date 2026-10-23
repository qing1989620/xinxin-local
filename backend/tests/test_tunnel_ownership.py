"""Tunnel controls must never stop unrelated processes or restart owner tasks."""
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_tunnel_entry_points_use_identity_checks_and_do_not_restart_local_tasks():
    start = (ROOT / "Start-Tunnel.ps1").read_text(encoding="utf-8-sig")
    stop = (ROOT / "Stop-Tunnel.ps1").read_text(encoding="utf-8-sig")
    for text in (start, stop):
        assert "Stop-XinxinTunnel $runtimePath" in text
        assert "Get-Process -Name" not in text
    assert "Stop-Xinxin-Local.ps1" not in start
    assert "start_ticks=$proc.StartTime.ToUniversalTime().Ticks" in start
    assert "executable=[System.IO.Path]::GetFullPath($tunnelExe)" in start


@pytest.mark.skipif(os.name != "nt" or not shutil.which("powershell.exe"), reason="Windows tunnel process identity")
def test_stale_pid_unverifiable_legacy_and_matching_tunnel_identity(tmp_path):
    script = tmp_path / "tunnel-test.ps1"
    script.write_text('''param([string]$Helper,[string]$Runtime)
$ErrorActionPreference='Stop'
. $Helper
New-Item -ItemType Directory -Path $Runtime -Force | Out-Null
$script:kills=0
$script:started=[datetime]'2026-10-23T01:00:00Z'
function Get-Process {param([int]$Id,[string]$ErrorAction)
  $proc=[pscustomobject]@{Id=$Id;StartTime=$script:started;Path='C:\\synthetic\\cloudflared.exe'}
  $proc | Add-Member ScriptMethod Kill {$script:kills++}
  $proc | Add-Member ScriptMethod WaitForExit {param($timeout) return $true}
  return $proc
}
$manifest=Join-Path $Runtime 'tunnel.json'
$url=Join-Path $Runtime 'public-url.txt'
@{role='tunnel';id=123;started='legacy'} | ConvertTo-Json | Set-Content -LiteralPath $manifest
try{Stop-XinxinTunnel $Runtime;throw 'Legacy identity was accepted'}catch{if($_.Exception.Message -notlike '*Cannot verify*'){throw}}
if($script:kills -ne 0 -or -not(Test-Path -LiteralPath $manifest)){throw 'Unverifiable process was changed'}
@{role='tunnel';id=123;start_ticks=$script:started.AddSeconds(-1).ToUniversalTime().Ticks;executable='C:\\synthetic\\cloudflared.exe'} | ConvertTo-Json | Set-Content -LiteralPath $manifest
'https://synthetic.invalid' | Set-Content -LiteralPath $url
if(Stop-XinxinTunnel $Runtime){throw 'Reused PID was killed'}
if($script:kills -ne 0 -or (Test-Path -LiteralPath $manifest) -or (Test-Path -LiteralPath $url)){throw 'Stale metadata cleanup failed'}
@{role='tunnel';id=123;start_ticks=$script:started.ToUniversalTime().Ticks;executable='C:\\unrelated.exe'} | ConvertTo-Json | Set-Content -LiteralPath $manifest
try{Stop-XinxinTunnel $Runtime;throw 'Wrong executable was accepted'}catch{if($_.Exception.Message -notlike '*differs*'){throw}}
if($script:kills -ne 0){throw 'Unrelated executable was killed'}
@{role='tunnel';id=123;start_ticks=$script:started.ToUniversalTime().Ticks;executable='C:\\synthetic\\cloudflared.exe'} | ConvertTo-Json | Set-Content -LiteralPath $manifest
if(-not(Stop-XinxinTunnel $Runtime)){throw 'Owned tunnel was not stopped'}
if($script:kills -ne 1 -or (Test-Path -LiteralPath $manifest)){throw 'Owned identity cleanup failed'}
Write-Output 'tunnel identity checks passed'
''', encoding="utf-8-sig")
    result = subprocess.run([shutil.which("powershell.exe"), "-NoProfile", "-File", str(script), str(ROOT / "desktop/Tunnel-State.ps1"), str(tmp_path / "runtime")], capture_output=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    assert b"tunnel identity checks passed" in result.stdout
