# -*- coding: utf-8 -*-
"""生成 Xinxin 电脑端图标资产（可复现）。

几何与 frontend/public/favicon.svg 完全一致：圆角方块 #376c62 + 交叉线 + 中心圆点 #faf8f0。
在 16 倍超采样画布上绘制后缩小到各尺寸，写成多图 ICO（PNG 压缩条目，Vista+ 全兼容）。

用法（项目 backend 虚拟环境自带 Pillow）：
    backend/.venv/Scripts/python.exe desktop/assets/make_icon.py
"""
from __future__ import annotations

import io
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 64  # favicon.svg 的 viewBox
SCALE = 16  # 超采样倍数
CANVAS = SIZE * SCALE

BG = (55, 108, 98, 255)        # #376c62
INK = (250, 248, 240, 255)     # #faf8f0

ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)
PREVIEW_SIZE = 512


def draw_mark(scale: int = SCALE) -> Image.Image:
    """按 favicon.svg 的几何绘制标志，返回 RGBA 位图。"""
    s = scale
    img = Image.new("RGBA", (SIZE * s, SIZE * s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, (SIZE - 1) * s, (SIZE - 1) * s], radius=16 * s, fill=BG)
    draw.line([(19 * s, 19 * s), (45 * s, 45 * s)], fill=INK, width=4 * s)
    draw.line([(45 * s, 19 * s), (19 * s, 45 * s)], fill=INK, width=4 * s)
    r = 7 * s
    cx = cy = 32 * s
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=INK)
    return img


def resized(master: Image.Image, size: int) -> Image.Image:
    return master.resize((size, size), Image.LANCZOS)


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def build_ico(images: list[tuple[int, bytes]]) -> bytes:
    """把 (size, png_bytes) 组装成多图 ICO。"""
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries = []
    blob = b""
    for size, data in images:
        width_byte = 0 if size >= 256 else size  # 256 在 ICO 里用 0 表示
        entries.append(
            struct.pack(
                "<BBBBHHII",
                width_byte,
                width_byte,
                0,   # 调色板颜色数（0 = 真彩色）
                0,   # 保留
                1,   # 色彩平面
                32,  # 位深
                len(data),
                offset,
            )
        )
        offset += len(data)
        blob += data
    return header + b"".join(entries) + blob


def main() -> int:
    here = Path(__file__).resolve().parent
    master = draw_mark()

    ico_images = [(size, png_bytes(resized(master, size))) for size in ICON_SIZES]
    ico_path = here / "xinxin.ico"
    ico_path.write_bytes(build_ico(ico_images))

    preview = resized(master, PREVIEW_SIZE)
    preview_path = here / "xinxin.png"
    preview.save(preview_path, format="PNG", optimize=True)

    total = sum(len(d) for _, d in ico_images)
    print(f"ico: {ico_path.name} ({len(ico_images)} sizes, {total} bytes payload)")
    print(f"png: {preview_path.name} ({preview_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
