"""Keep module-level ASGI initialization out of the owner's running database."""

import os
import uuid
from pathlib import Path

os.environ["XINXIN_DATA_DIR"] = str(
    Path(__file__).resolve().parents[1]
    / ".qa-data"
    / ("pytest-import-" + uuid.uuid4().hex)
)
# Agent lifecycle tests script exact model responses; the optional Fabric rerank
# would consume the first scripted call. Routing algorithms are covered by
# test_skillnet_fabric.py and the live smoke script instead.
os.environ.setdefault("XINXIN_SKILLNET_RERANK", "0")
