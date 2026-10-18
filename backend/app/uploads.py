"""Guard upload ingress before FastAPI parses/spools multipart data."""

from __future__ import annotations

import asyncio

from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.formparsers import MultiPartException
from starlette.responses import JSONResponse

from .files import MAX_UPLOAD

MAX_BODY_BYTES = MAX_UPLOAD + 256 * 1024


class UploadGuard:
    def __init__(self, app, auth):
        self.app, self.auth = app, auth
        self.slots = asyncio.Semaphore(2)

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] != "http"
            or scope["method"] != "POST"
            or scope["path"] != "/api/v1/files"
        ):
            return await self.app(scope, receive, send)
        headers = Headers(scope=scope)
        try:
            self.auth.require(headers.get("authorization"))
        except HTTPException as exc:
            return await JSONResponse(
                {"detail": exc.detail}, status_code=exc.status_code
            )(scope, receive, send)
        length = headers.get("content-length")
        if length:
            try:
                length = int(length)
            except ValueError:
                return await JSONResponse(
                    {"detail": "上传请求长度无效"}, status_code=400
                )(scope, receive, send)
            if length < 0 or length > MAX_BODY_BYTES:
                return await JSONResponse(
                    {"detail": "文件超过 64 MB 上传上限"}, status_code=413
                )(scope, receive, send)
        total, exceeded, replied = 0, False, False

        async def bounded_receive():
            nonlocal total, exceeded
            message = await receive()
            if message["type"] == "http.disconnect":
                raise MultiPartException("上传连接已中断")
            if message["type"] == "http.request":
                total += len(message.get("body", b""))
                if total > MAX_BODY_BYTES:
                    exceeded = True
                    # Starlette closes partially spooled files on this error.
                    raise MultiPartException("上传请求超过大小限制")
            return message

        async def bounded_send(message):
            nonlocal replied
            if exceeded:
                if not replied:
                    replied = True
                    await JSONResponse(
                        {"detail": "文件超过 64 MB 上传上限"}, status_code=413
                    )(scope, receive, send)
                return
            await send(message)

        async with self.slots:
            await self.app(scope, bounded_receive, bounded_send)


async def finish_upload(worker):
    """Retain the source and request slot until the background thread finishes."""
    try:
        return await asyncio.shield(worker)
    except asyncio.CancelledError:
        while not worker.done():
            try:
                await asyncio.shield(worker)
            except asyncio.CancelledError:
                continue
            except Exception:  # noqa: BLE001 -- caller cancellation remains the outcome; retrieve failure below.
                break
        if worker.done() and not worker.cancelled():
            worker.exception()
        raise
