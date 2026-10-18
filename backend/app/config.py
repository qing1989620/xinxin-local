from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_CALLS = 64
DEFAULT_TASK_SECONDS = 3600
TOKENS_PER_MODEL_CALL = 125000
CONTEXT_WINDOW_TOKENS = 1048576
CONTEXT_TIERS = (80000, 300000, CONTEXT_WINDOW_TOKENS)
CONTEXT_INPUT_TOKENS = CONTEXT_WINDOW_TOKENS - 32768
MAX_SYSTEM_PROMPT_CHARS = 16000
load_dotenv(ROOT / ".env", override=False)


@dataclass
class Config:
    data_dir: Path
    setup_token: str
    model: str = "deepseek-flash"
    model_url: str = "https://api.deepseek.com/chat/completions"
    api_key: str = ""
    origins: tuple[str, ...] = ()
    task_concurrency: int = 1

    @classmethod
    def from_env(cls):
        raw = Path(os.getenv("XINXIN_DATA_DIR", "data"))
        data = (raw if raw.is_absolute() else ROOT / raw).resolve()
        data.mkdir(parents=True, exist_ok=True)
        code_file = data / "bootstrap.code"
        code = os.getenv("XINXIN_SETUP_TOKEN", "")
        if not code:
            if not code_file.exists():
                code_file.write_text(secrets.token_urlsafe(24), encoding="utf-8")
                try:
                    code_file.chmod(0o600)
                except OSError:
                    pass
            code = code_file.read_text(encoding="utf-8").strip()
        origins = tuple(
            x.strip()
            for x in os.getenv(
                "XINXIN_CORS_ORIGINS",
                "http://localhost:5188,http://127.0.0.1:5188,http://localhost:5173,http://127.0.0.1:5173,https://localhost,http://localhost,capacitor://localhost",
            ).split(",")
            if x.strip()
        )
        return cls(
            data,
            code,
            os.getenv("XINXIN_MODEL", "deepseek-flash"),
            os.getenv("XINXIN_MODEL_URL", "https://api.deepseek.com/chat/completions"),
            os.getenv("DEEPSEEK_API_KEY", ""),
            origins,
            max(1, min(4, int(os.getenv("XINXIN_TASK_CONCURRENCY", "1")))),
        )
