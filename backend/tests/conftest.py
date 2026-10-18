"""Keep module-level ASGI initialization out of the owner's running database."""

import os
import uuid
from pathlib import Path

os.environ["XINXIN_DATA_DIR"] = str(
    Path(__file__).resolve().parents[1]
    / ".qa-data"
    / ("pytest-import-" + uuid.uuid4().hex)
)
