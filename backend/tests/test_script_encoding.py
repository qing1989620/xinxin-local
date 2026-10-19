"""Guard against the Windows PowerShell 5.1 encoding trap.

Windows PowerShell decodes a BOM-less .ps1 as GBK on this machine, so a script
that contains Chinese text but no UTF-8 BOM fails to parse (a stray byte turns
into an unterminated string). Keep every non-ASCII script BOM-marked.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _script_roots() -> list[Path]:
    roots = [ROOT]
    # 电脑软件端的脚本同样含中文，一并纳入守卫
    desktop = ROOT / "desktop"
    if desktop.is_dir():
        roots.append(desktop)
    return roots


def test_non_ascii_powershell_scripts_have_utf8_bom():
    offenders = []
    for root in _script_roots():
        for path in sorted(root.glob("*.ps1")):
            data = path.read_bytes()
            if any(byte > 127 for byte in data) and not data.startswith(b"\xef\xbb\xbf"):
                offenders.append(path.name)
    assert not offenders, f"missing UTF-8 BOM: {offenders}"


def test_powershell_scripts_are_not_empty():
    scripts = [path for root in _script_roots() for path in root.glob("*.ps1") if path.stat().st_size > 0]
    assert scripts
