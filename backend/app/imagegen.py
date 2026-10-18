"""文生图：默认 Pollinations（免费、无需密钥），可选 OpenRouter（自带密钥）。

设计要点：
- Pollinations 是默认档：无需账号、无需密钥，直接 GET 图片字节。
  密钥类服务只在用户配置了 OPENROUTER_API_KEY 后作为可选项出现。
- 产物统一落盘到文件库（mime=image/*），与上传文件同一套下载/删除通路。
- 只接受真正的图片字节（JPEG/PNG/WebP 魔数校验），拒绝把错误页
  或限流文案当成图片保存。
"""

from __future__ import annotations

import base64
import os
import re
import urllib.parse

import httpx

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_IMAGE_MODEL = "google/gemini-3.1-flash-lite-image"

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_PROMPT_CHARS = 2000
TIMEOUT = httpx.Timeout(240.0, connect=20.0)

_IMAGE_MAGIC = (
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"RIFF", "webp"),
)


def _detect_image(content: bytes) -> str | None:
    for magic, kind in _IMAGE_MAGIC:
        if content.startswith(magic):
            if kind == "webp" and content[8:12] != b"WEBP":
                continue
            return kind
    return None


def _proxy() -> str | None:
    return os.getenv("XINXIN_HTTP_PROXY") or os.getenv("HTTPS_PROXY") or None


def _client() -> httpx.Client:
    return httpx.Client(timeout=TIMEOUT, follow_redirects=True, trust_env=True)


def _slug(text: str, limit: int = 24) -> str:
    ascii_only = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return ascii_only[:limit] or "image"


DEFAULT_PROVIDER = "pollinations"


def providers() -> dict:
    """可用档位：Pollinations 始终可用；OpenRouter 需要密钥。

    注意：OpenRouter 的图像模型实测（2026-10）无一免费档，
    账户余额为 0 时调用必返回 402，因此文案必须如实说明"需要余额"，
    不能让用户误以为填了密钥就能免费用。
    """
    key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    return {
        "default": DEFAULT_PROVIDER,
        "pollinations": {
            "available": True,
            "label": "Pollinations · 免费无需密钥",
            "model": "flux",
        },
        "openrouter": {
            "available": bool(key),
            "label": "OpenRouter · 需要密钥和账户余额",
            "model": os.getenv("OPENROUTER_IMAGE_MODEL") or DEFAULT_OPENROUTER_IMAGE_MODEL,
            "reason": None if key else "未配置 OPENROUTER_API_KEY",
        },
    }


def _validate_prompt(prompt: str) -> str:
    prompt = (prompt or "").strip()
    if not prompt:
        raise ValueError("请描述想画的画面")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ValueError(f"描述过长（最多 {MAX_PROMPT_CHARS} 字）")
    return prompt


def _check_image(content: bytes) -> tuple[str, str]:
    kind = _detect_image(content)
    if kind is None:
        snippet = content[:120].decode("utf-8", errors="replace").strip()
        raise ValueError(f"上游没有返回图片（{snippet[:80] or '未知内容'}）")
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError("图片超过 20 MB 上限")
    mime = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}[kind]
    return kind, mime


def _pollinations(prompt: str, width: int, height: int, seed: int | None) -> tuple[bytes, str, str]:
    query = {
        "width": width,
        "height": height,
        "nologo": "true",
        "model": os.getenv("POLLINATIONS_MODEL") or "flux",
    }
    if seed is not None:
        query["seed"] = seed
    url = POLLINATIONS_URL + urllib.parse.quote(prompt) + "?" + urllib.parse.urlencode(query)
    with _client() as client:
        response = client.get(url)
    if response.status_code != 200:
        raise ValueError(f"Pollinations 返回 {response.status_code}，稍后重试")
    kind, mime = _check_image(response.content)
    return response.content, kind, mime


def _image_bytes_from_payload(image: dict) -> str:
    """从 OpenRouter 返回的图片对象里取 base64 数据。

    兼容两种上游形状：
    - 旧式：{"image_url": {"url": "data:image/png;base64,...."}}
    - 新式：{"b64_json": "...."}
    """
    url = ""
    image_url = image.get("image_url")
    if isinstance(image_url, dict):
        url = image_url.get("url") or ""
    elif isinstance(image_url, str):
        url = image_url
    if url.startswith("data:"):
        return url.split(",", 1)[1] if "," in url else ""
    b64 = image.get("b64_json") or ""
    return b64 if isinstance(b64, str) else ""


def _openrouter(prompt: str) -> tuple[bytes, str, str]:
    key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if not key:
        raise ValueError("未配置 OPENROUTER_API_KEY，暂时只能用免费档 Pollinations")
    model = os.getenv("OPENROUTER_IMAGE_MODEL") or DEFAULT_OPENROUTER_IMAGE_MODEL
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["image", "text"],
    }
    headers = {"Authorization": f"Bearer {key}"}
    proxy = _proxy()
    with httpx.Client(timeout=TIMEOUT, trust_env=True, proxy=proxy) as client:
        response = client.post(OPENROUTER_URL, json=payload, headers=headers)
    if response.status_code != 200:
        detail = response.text[:200]
        raise ValueError(f"OpenRouter 返回 {response.status_code}：{detail}")
    data = response.json()
    images = (
        (data.get("choices") or [{}])[0]
        .get("message", {})
        .get("images")
        or []
    )
    if not images:
        raise ValueError("模型没有返回图片，换个描述再试")
    encoded = _image_bytes_from_payload(images[0] if isinstance(images[0], dict) else {})
    if not encoded:
        raise ValueError("模型返回的不是内嵌图片数据")
    try:
        content = base64.b64decode(encoded, validate=False)
    except Exception:
        raise ValueError("图片数据解码失败") from None
    kind, mime = _check_image(content)
    return content, kind, mime


def generate(library, prompt: str, width=1024, height=1024, provider=None, seed=None):
    """生成图片并登记到文件库。返回文件记录 + 生成信息。"""
    prompt = _validate_prompt(prompt)
    width = max(256, min(1440, int(width or 1024)))
    height = max(256, min(1440, int(height or 1024)))
    available = providers()
    # 归一化：None / "" / "default" 都回到默认档；再按两个真实档位校验，
    # 否则字符串档位对字典取键会抛 TypeError 变成 500。
    provider = (provider or "").strip().lower() or available["default"]
    if provider == "default":
        provider = available["default"]
    if provider not in ("pollinations", "openrouter"):
        raise ValueError(f"未知生图档位：{provider}")
    if not available[provider]["available"]:
        raise ValueError(available[provider].get("reason") or "该档位不可用")

    if provider == "openrouter":
        content, kind, mime = _openrouter(prompt)
        model = available["openrouter"]["model"]
    else:
        content, kind, mime = _pollinations(prompt, width, height, seed)
        model = available["pollinations"]["model"]

    name = f"xinxin-{_slug(prompt)}-{kind}.{'jpg' if kind == 'jpg' else kind}"
    record = library.save(name, content, mime=mime, extract=False)
    return {
        **record,
        "image": {
            "prompt": prompt,
            "provider": provider,
            "model": model,
            "width": width,
            "height": height,
            "seed": seed,
            "bytes": len(content),
        },
    }


def recent(library, limit=60):
    """最近生成的图片（文件库中 image/* 且名字带 xinxin- 前缀）。"""
    limit = max(1, min(200, int(limit or 60)))
    with library.store.connect() as db:
        rows = db.execute(
            "SELECT id AS file_id,name,mime,size AS bytes,created FROM files "
            "WHERE mime LIKE 'image/%' AND name LIKE 'xinxin-%' "
            "ORDER BY created DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
