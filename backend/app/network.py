"""Local address book.

Everything here is read from files this machine writes while starting the
services (`.runtime/addresses.json`, `.runtime/public-url.txt`). No external
service is consulted; the LAN address works with no internet at all.
"""

from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .config import ROOT


def runtime_dir() -> Path:
    override = os.getenv("XINXIN_RUNTIME_DIR")
    return Path(override) if override else ROOT.parent / ".runtime"


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text("utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _public_url(path: Path) -> tuple[str, str]:
    """Only a bare HTTPS origin is accepted; anything else is ignored."""
    try:
        raw = path.read_text("utf-8-sig").strip()
    except OSError:
        return "", ""
    try:
        parts = urlsplit(raw)
    except ValueError:
        return "", ""
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username
        or parts.password
        or parts.query
        or parts.fragment
    ):
        return "", ""
    try:
        updated = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    except OSError:
        updated = ""
    return raw.rstrip("/"), updated


def _detect_lan(port: int) -> str:
    """UDP connect only selects a route; it does not send a packet."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("223.5.5.5", 80))
        address = sock.getsockname()[0]
    except OSError:
        address = ""
    finally:
        sock.close()
    if not address or address.startswith("127.") or address.startswith("169.254."):
        return ""
    return f"http://{address}:{port}"


def local_addresses() -> dict:
    runtime = runtime_dir()
    saved = _read_json(runtime / "addresses.json")
    gateway_port = saved.get("gateway_port")
    if not isinstance(gateway_port, int) or not 1 <= gateway_port <= 65535:
        try:
            gateway_port = int(os.getenv("XINXIN_GATEWAY_PORT", "8080"))
        except ValueError:
            gateway_port = 8080
    lan = saved.get("lan")
    if not isinstance(lan, str) or not lan.startswith("http://"):
        lan = _detect_lan(gateway_port)
    local = saved.get("local")
    if not isinstance(local, str) or not local.startswith("http://"):
        local = f"http://127.0.0.1:{os.getenv('XINXIN_FRONTEND_PORT', '5180')}"
    public, updated = _public_url(runtime / "public-url.txt")
    return {
        "local": local,
        "lan": lan,
        "public": public,
        "gateway_port": gateway_port,
        "public_updated": updated,
        "server_required": False,
    }
