"""Actual PowerShell 5.1 redirection, as used by the desktop caller."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
POWERSHELL = shutil.which("powershell.exe")
pytestmark = pytest.mark.skipif(os.name != "nt" or not POWERSHELL, reason="Windows PowerShell 5.1")


def test_native_warnings_are_logged_but_nonzero_exit_still_fails(tmp_path):
    native = tmp_path / "native.py"
    native.write_text("import sys\nprint('正常构建输出')\nsys.stderr.write('warning: 合成构建警告\\n')\nsys.exit(int(sys.argv[1]))\n", encoding="utf-8")
    script = tmp_path / "caller.ps1"
    script.write_text('''param([string]$Helper,[string]$Python,[string]$Native,[string]$Output)
$ErrorActionPreference='Stop'
. $Helper
$encoding=[Console]::OutputEncoding.CodePage
Invoke-XinxinNative $Python @('-X','utf8',$Native,'0') 'synthetic build failed' *>> $Output
if($ErrorActionPreference -ne 'Stop' -or [Console]::OutputEncoding.CodePage -ne $encoding){throw 'Caller state was not restored'}
$failed=$false
try {Invoke-XinxinNative $Python @('-X','utf8',$Native,'7') 'synthetic build failed' *>> $Output}
catch {if($_.Exception.Message -notlike '*synthetic build failed (exit 7)*'){throw};$failed=$true}
if(-not $failed){throw 'Native failure was hidden'}
''', encoding="utf-8-sig")
    output = tmp_path / "build.txt"
    response = subprocess.run([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), str(ROOT / "desktop/Local-ServiceState.ps1"), sys.executable, str(native), str(output)], capture_output=True, timeout=30)
    assert response.returncode == 0, response.stdout + response.stderr
    text = output.read_text(encoding="utf-16")
    assert "正常构建输出" in text and "合成构建警告" in text


def test_error_page_preserves_utf8_template_and_log(tmp_path):
    (tmp_path / "runtime").mkdir()
    log = tmp_path / "desktop.log"
    log.write_text("中文诊断日志\n", encoding="utf-8")
    script = tmp_path / "error-page.ps1"
    script.write_text('''param([string]$Source,[string]$Assets,[string]$Runtime,[string]$Log)
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($Source,[ref]$tokens,[ref]$errors)
$definition=$ast.FindAll({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Show-ErrorWindow'},$true)[0]
. ([scriptblock]::Create($definition.Extent.Text))
$assetsPath=$Assets;$runtimePath=$Runtime;$logPath=$Log
function Protect-Html([string]$Text){[System.Net.WebUtility]::HtmlEncode($Text)}
function Get-EdgePath {return $null}
Show-ErrorWindow '合成启动失败'
''', encoding="utf-8-sig")
    response = subprocess.run([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), str(ROOT / "desktop/Xinxin-Desktop.ps1"), str(ROOT / "desktop/assets"), str(tmp_path / "runtime"), str(log)], capture_output=True, timeout=20)
    assert response.returncode == 0, response.stdout + response.stderr
    html = (tmp_path / "runtime/desktop-error.html").read_text(encoding="utf-8")
    assert "这次没能启动" in html and "合成启动失败" in html and "中文诊断日志" in html
