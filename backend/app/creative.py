from __future__ import annotations

import base64
import io
import json
import threading
from pathlib import Path

import httpx

from .config import ROOT
from .model import endpoint
from .store import uid

PLOT_LOCK = threading.Lock()


def gallery():
    result = []
    root = ROOT / "resources" / "plot" / "gallery"
    for path in sorted(root.glob("*.png")):
        card = path.with_suffix(".md")
        if not card.exists():
            continue
        import yaml

        metadata = (
            yaml.safe_load(card.read_text(encoding="utf-8").split("---", 2)[1]) or {}
        )
        result.append(
            {
                "id": path.stem,
                "title": metadata.get("title", path.stem),
                "kind": metadata.get("kind"),
                "purpose": metadata.get("purpose", []),
                "palettes": metadata.get("palettes", []),
                "has_code": path.with_suffix(".py").exists(),
            }
        )
    return sorted(result, key=lambda row: not row["has_code"])


def plot_csv(
    library,
    file_id,
    x,
    y,
    kind="line",
    title="Data study",
    palette="teal",
    run_id=None,
    cancelled=None,
):
    import inspect
    import pandas as pd
    from .figure_recipe import render_figure

    if cancelled and cancelled.is_set():
        raise RuntimeError("绘图已取消")
    frame = pd.read_csv(library.path(file_id), nrows=100000)
    colors = {
        "teal": "#256d63",
        "clay": "#b65b43",
        "indigo": "#555e99",
        "ink": "#333c43",
    }
    recipe = {
        "x": x,
        "y": y,
        "kind": kind,
        "title": title[:100],
        "color": colors.get(palette, colors["teal"]),
    }
    with PLOT_LOCK:
        rendered = render_figure(frame, recipe, cancelled)
    script = (
        "# Xinxin: same renderer and styling as the platform.\n# Run: python xinxin-figure.py [original.csv]\nimport argparse, json\nfrom pathlib import Path\nimport pandas as pd\n\n"
        + inspect.getsource(render_figure)
        + "\nif __name__ == '__main__':\n    parser=argparse.ArgumentParser()\n    parser.add_argument('csv',nargs='?',default='input.csv')\n    args=parser.parse_args()\n    recipe=json.loads("
        + repr(json.dumps(recipe, ensure_ascii=False))
        + ")\n    output=render_figure(pd.read_csv(args.csv,nrows=100000),recipe)\n    for ext in ('png','pdf'):\n        Path('figure.'+ext).write_bytes(output[ext])\n"
    )
    if cancelled and cancelled.is_set():
        raise RuntimeError("绘图已取消")
    outputs = [
        library.save(
            "xinxin-figure." + ext, rendered[ext], run_id=run_id, extract=False
        )
        for ext in ("png", "pdf")
    ]
    outputs.append(library.save("xinxin-figure.py", script.encode(), run_id=run_id))
    return {"files": outputs, "rows": rendered["rows"], "source_file_id": file_id}


async def transform_image(
    library, auth, file_id, style, instruction, run_id=None, transport=None
):
    names = {
        "collage": "scenes-gathered-zine-v1-3",
        "distillation": "scene-distillation-zine-v1-3",
    }
    if style not in names:
        raise ValueError("未知转换方式")
    url = auth.store.setting("image_url", "")
    key = auth.secret("image_api_key")
    model = auth.store.setting("image_model", "gpt-image-1")
    if not url or not key:
        raise ValueError(
            "请先在设置中配置图像生成服务；DeepSeek 对话接口不负责图片生成"
        )
    skill = auth.store.directory / "skills" / names[style] / "SKILL.md"
    if not skill.exists():
        raise ValueError("拾景技能尚未安装，请运行后端的可选技能安装脚本")
    path = library.path(file_id)
    from PIL import Image

    with Image.open(path) as im:
        if im.width * im.height > 40_000_000:
            raise ValueError("图片像素过大")
        im.verify()
    prompt = (
        skill.read_text(encoding="utf-8") + "\n\nUser direction: " + instruction[:3000]
    )
    async with httpx.AsyncClient(
        timeout=300, transport=transport, follow_redirects=False
    ) as client:
        with path.open("rb") as image:
            response = await client.post(
                endpoint(url),
                headers={"Authorization": "Bearer " + key},
                data={"model": model, "prompt": prompt, "n": "1"},
                files={
                    "image": (
                        "reference" + path.suffix,
                        image,
                        library.get(file_id)["mime"],
                    )
                },
            )
        if response.status_code >= 300:
            raise ValueError(f"图像服务返回异常状态 {response.status_code}")
        item = response.json().get("data", [{}])[0]
        if not item.get("b64_json"):
            raise ValueError(
                "图像接口需返回 b64_json；未自动访问服务返回的外部下载地址"
            )
        image_data = base64.b64decode(item["b64_json"], validate=True)
        result = library.save(
            "xinxin-zine.png", image_data, "image/png", run_id, extract=False
        )
        return {
            "files": [result],
            "style": style,
            "credit": "Visual Skill by @Zeejay0",
            "source_sent_to_configured_image_service": True,
        }
