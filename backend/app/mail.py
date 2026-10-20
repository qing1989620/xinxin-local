"""Single-owner email codes. No registration and no plaintext codes at rest.

Adapted design: lankhub email/verify-code.ts (MIT), pinned in THIRD_PARTY.md.
Two transports: TLS SMTP (default) or Resend's HTTP API called directly with
httpx — no SDK, no extra dependency. Resend also exposes domain management so
the owner can send from a verified custom domain.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import smtplib
import ssl
import time
from email.message import EmailMessage

import httpx
from fastapi import HTTPException

from .store import uid

RESEND_API = "https://api.resend.com"


class MailCodes:
    def __init__(self, store, auth):
        self.store, self.auth = store, auth
        key = auth.secret("email_hmac_key")
        if not key:
            key = secrets.token_hex(32)
            auth.set_secret("email_hmac_key", key)
        self.key = key.encode()
        with store.connect(write=True) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS email_codes(
                id TEXT PRIMARY KEY, scene TEXT NOT NULL, digest TEXT NOT NULL,
                expires REAL NOT NULL, created REAL NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                used INTEGER NOT NULL DEFAULT 0, peer_hash TEXT NOT NULL)""")
            db.execute(
                "CREATE INDEX IF NOT EXISTS email_codes_created ON email_codes(created)"
            )

    def enabled(self):
        config = self.configuration()
        if not config["email"] or not self.store.one("SELECT id FROM owner"):
            return False
        if config["provider"] == "resend":
            return bool(config["resend_api_key"] and config["resend_from"])
        return bool(config["smtp_password"])

    def configuration(self):
        # A single SELECT observes one committed set of credentials.
        rows = {
            row["key"]: json.loads(row["value"])
            for row in self.store.all(
                "SELECT key,value FROM settings WHERE key IN ("
                "'email_provider','secret:owner_email','secret:smtp_username',"
                "'secret:smtp_password','smtp_host','smtp_port','smtp_mode',"
                "'resend_from','secret:resend_api_key')"
            )
        }

        def secret(name):
            value = rows.get("secret:" + name)
            return self.auth.vault.decrypt(value.encode()).decode() if value else ""

        email = secret("owner_email")
        provider = rows.get("email_provider", "smtp")
        return {
            "provider": provider if provider in {"smtp", "resend"} else "smtp",
            "email": email,
            "smtp_username": secret("smtp_username") or email,
            "smtp_password": secret("smtp_password"),
            "smtp_host": rows.get("smtp_host", "smtp.qq.com"),
            "smtp_port": rows.get("smtp_port", 465),
            "smtp_mode": rows.get("smtp_mode", "ssl"),
            "resend_from": rows.get("resend_from", ""),
            "resend_api_key": secret("resend_api_key"),
        }

    def configure(self, values):
        email = values["email"].strip().lower()
        provider = values.get("provider", "smtp")
        resend_from = (values.get("resend_from") or "").strip()
        if provider == "resend" and resend_from and not re.search(
            r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}>?\s*$",
            resend_from,
        ):
            raise HTTPException(400, "发件人格式应为：Xinxin <no-reply@你的域名>")
        plain = {
            "email_provider": provider,
            "smtp_host": values["smtp_host"],
            "smtp_port": values["smtp_port"],
            "smtp_mode": values["smtp_mode"],
            "resend_from": resend_from,
        }
        to_save = {
            "owner_email": email,
            "smtp_username": values["smtp_username"] or email,
        }
        if values["smtp_password"]:
            to_save["smtp_password"] = values["smtp_password"]
        if values.get("resend_api_key"):
            to_save["resend_api_key"] = values["resend_api_key"]
        encrypted = {
            "secret:" + key: self.auth.vault.encrypt(value.encode()).decode()
            for key, value in to_save.items()
        }
        with self.store.connect(write=True) as db:
            db.executemany(
                "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                [
                    (key, json.dumps(value))
                    for key, value in {**plain, **encrypted}.items()
                ],
            )
            db.execute("UPDATE email_codes SET used=1")

    def digest(self, email, scene, code):
        return hmac.new(
            self.key, f"{email}:{scene}:{code}".encode(), hashlib.sha256
        ).hexdigest()

    def send(self, email, scene, peer):
        if not self.enabled():
            raise HTTPException(503, "邮箱服务尚未配置，请先使用账号密码登录")
        # Do not reveal the owner's address from an anonymous endpoint.
        recipient = self.auth.secret("owner_email").strip().lower()
        if not hmac.compare_digest(email.encode(), recipient.encode()):
            return {
                "ok": True,
                "retry_after": 60,
                "message": "若邮箱匹配主人账号，验证码将发送到该邮箱",
            }
        current, ident = time.time(), uid()
        code = f"{secrets.randbelow(1000000):06d}"
        peer_hash = hmac.new(self.key, peer.encode(), hashlib.sha256).hexdigest()
        with self.store.connect(write=True) as db:
            last = db.execute(
                "SELECT created FROM email_codes ORDER BY created DESC LIMIT 1"
            ).fetchone()
            if last and current - last["created"] < 60:
                raise HTTPException(
                    429,
                    "请等待 60 秒后再获取验证码",
                    headers={
                        "Retry-After": str(max(1, int(60 - current + last["created"])))
                    },
                )
            daily = db.execute(
                "SELECT COUNT(*) FROM email_codes WHERE created>?", (current - 86400,)
            ).fetchone()[0]
            monthly = db.execute(
                "SELECT COUNT(*) FROM email_codes WHERE created>?",
                (current - 30 * 86400,),
            ).fetchone()[0]
            if daily >= 10 or monthly >= 100:
                raise HTTPException(429, "已达到邮件发送配额，请稍后再试")
            db.execute(
                "DELETE FROM email_codes WHERE created<?", (current - 31 * 86400,)
            )
            db.execute(
                "UPDATE email_codes SET used=1 WHERE scene=? AND used=0", (scene,)
            )
            db.execute(
                "INSERT INTO email_codes(id,scene,digest,expires,created,peer_hash) VALUES(?,?,?,?,?,?)",
                (
                    ident,
                    scene,
                    self.digest(email, scene, code),
                    current + 600,
                    current,
                    peer_hash,
                ),
            )
        try:
            self._send(recipient, code, scene)
        except Exception as failure:  # noqa: BLE001 -- 上游失败一律转成可读提示
            self.store.execute("UPDATE email_codes SET used=1 WHERE id=?", (ident,))
            if isinstance(failure, RuntimeError) and str(failure).startswith("Resend"):
                raise HTTPException(
                    503,
                    f"邮件发送失败（{str(failure)[:80]}），请检查 Resend 配置；账号密码登录仍可使用",
                ) from None
            raise HTTPException(
                503, "邮件发送失败，请检查 SMTP 配置后重试；账号密码登录仍可使用"
            ) from None
        self.store.audit("email.sent", {"scene": scene})
        return {
            "ok": True,
            "retry_after": 60,
            "message": "若邮箱匹配主人账号，验证码将发送到该邮箱",
        }

    def _send(self, recipient, code, scene):
        config = self.configuration()
        if config["email"].strip().lower() != recipient:
            raise RuntimeError("邮件配置已改变，请重新获取验证码")
        subject = "Xinxin · " + ("登录验证码" if scene == "login" else "重置密码验证码")
        text = (
            f'你的 Xinxin 验证码是：{code}\n\n'
            f'此验证码 10 分钟内有效，仅可使用一次。\n'
            f'用途：{"登录" if scene == "login" else "重置密码"}。\n'
            f'如果这次操作不是你发起的，请忽略此邮件。'
        )
        if config["provider"] == "resend":
            self._send_resend(config, recipient, subject, text, self._code_html(code, scene))
        else:
            self._send_smtp(config, recipient, subject, text)

    def test_delivery(self):
        """配置后台测试发信：只发给绑定邮箱，不占用验证码配额。"""
        config = self.configuration()
        recipient = config["email"].strip().lower()
        if not recipient:
            raise HTTPException(400, "请先填写绑定邮箱并保存")
        if not self.enabled():
            missing = (
                "Resend API Key 与发件人"
                if config["provider"] == "resend"
                else "SMTP 授权码"
            )
            raise HTTPException(400, f"还缺{missing}，请先保存完整配置")
        subject = "Xinxin · 配置测试"
        text = (
            "这是一封配置测试邮件。\n\n"
            "收到它说明 Xinxin 的验证码邮件通道已经可用；"
            "之后登录和找回密码都可以用邮箱验证码。\n"
            "如果这不是你发起的操作，请忽略此邮件。"
        )
        html = (
            '<div style="font-family:system-ui,-apple-system,\'PingFang SC\',sans-serif;'
            'max-width:520px;margin:0 auto;padding:32px 24px;color:#292e2b">'
            '<p style="font-size:12px;letter-spacing:.18em;color:#626d64;margin:0 0 18px">'
            "XINXIN · A SPACE OF YOUR OWN</p>"
            '<h1 style="font-size:22px;font-weight:550;margin:0 0 14px">邮件通道测试</h1>'
            '<p style="font-size:13px;line-height:1.9;color:#626d64;margin:0">'
            "收到这封邮件说明验证码通道可用；之后登录和找回密码都可以用邮箱验证码。</p>"
            "</div>"
        )
        try:
            if config["provider"] == "resend":
                self._send_resend(config, recipient, subject, text, html)
            else:
                self._send_smtp(config, recipient, subject, text)
        except Exception as failure:  # noqa: BLE001 -- 上游失败一律转成可读提示
            self.store.audit("email.test_failed", {"provider": config["provider"]})
            if isinstance(failure, RuntimeError) and str(failure).startswith("Resend"):
                raise HTTPException(
                    503, f"发信失败（{str(failure)[:80]}），请检查 Resend 配置"
                ) from None
            raise HTTPException(
                503, "发信失败，请检查 SMTP 服务器、端口、加密方式与授权码"
            ) from None
        self.store.audit("email.tested", {"provider": config["provider"]})
        return {"ok": True, "provider": config["provider"], "to": recipient}

    def _send_smtp(self, config, recipient, subject, text):
        host, port = config["smtp_host"], config["smtp_port"]
        username, mode, password = (
            config["smtp_username"],
            config["smtp_mode"],
            config["smtp_password"],
        )
        message = EmailMessage()
        message["From"] = username
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(text)
        context = ssl.create_default_context()
        if mode == "ssl":
            connection = smtplib.SMTP_SSL(host, port, timeout=10, context=context)
        else:
            connection = smtplib.SMTP(host, port, timeout=10)
        with connection as smtp:
            if mode == "starttls":
                smtp.starttls(context=context)
            smtp.login(username, password)
            smtp.send_message(message)

    @staticmethod
    def _code_html(code, scene):
        return (
            '<div style="font-family:system-ui,-apple-system,\'PingFang SC\',sans-serif;'
            'max-width:520px;margin:0 auto;padding:32px 24px;color:#292e2b">'
            '<p style="font-size:12px;letter-spacing:.18em;color:#626d64;margin:0 0 18px">'
            "XINXIN · A SPACE OF YOUR OWN</p>"
            '<h1 style="font-size:22px;font-weight:550;margin:0 0 14px">'
            f'{"登录" if scene == "login" else "重置密码"}验证码</h1>'
            f'<p style="font-size:30px;letter-spacing:8px;margin:18px 0;font-weight:600">{code}</p>'
            '<p style="font-size:13px;line-height:1.8;color:#626d64;margin:0">'
            "10 分钟内有效，仅可使用一次。如果这次操作不是你发起的，请忽略此邮件。</p>"
            "</div>"
        )

    def _send_resend(self, config, recipient, subject, text, html):
        """Resend HTTP API，直调不引 SDK；失败只保留状态码与错误名。"""
        response = httpx.post(
            RESEND_API + "/emails",
            headers={"Authorization": "Bearer " + config["resend_api_key"]},
            json={
                "from": config["resend_from"],
                "to": [recipient],
                "subject": subject,
                "text": text,
                "html": html,
            },
            timeout=20,
        )
        if response.status_code >= 300:
            detail = ""
            try:
                payload = response.json()
                detail = str(payload.get("name") or payload.get("message") or "")
            except ValueError:
                pass
            raise RuntimeError(
                f"Resend {response.status_code} {detail}".strip()[:200]
            )

    # ------------------------------------------------------------------
    # Resend 域名管理（用于"用自己域名发信"）
    # ------------------------------------------------------------------
    def _resend_headers(self):
        key = self.auth.secret("resend_api_key")
        if not key:
            raise HTTPException(400, "请先在设置中保存 Resend API Key")
        return {"Authorization": "Bearer " + key}

    def domains(self):
        response = httpx.get(
            RESEND_API + "/domains", headers=self._resend_headers(), timeout=20
        )
        if response.status_code == 401:
            raise HTTPException(400, "Resend API Key 无效或已被撤销")
        if response.status_code >= 300:
            raise HTTPException(502, f"读取域名失败（{response.status_code}）")
        data = response.json().get("data") or []
        return [
            {
                "id": row.get("id"),
                "name": row.get("name"),
                "status": row.get("status"),
                "region": row.get("region"),
                "created_at": row.get("created_at"),
                "records": [
                    {
                        "record": record.get("record"),
                        "name": record.get("name"),
                        "type": record.get("type"),
                        "value": record.get("value"),
                        "ttl": record.get("ttl"),
                        "priority": record.get("priority"),
                        "status": record.get("status"),
                    }
                    for record in (row.get("records") or [])
                ],
            }
            for row in data
        ]

    def add_domain(self, name):
        response = httpx.post(
            RESEND_API + "/domains",
            headers=self._resend_headers(),
            json={"name": name},
            timeout=25,
        )
        if response.status_code == 401:
            raise HTTPException(400, "Resend API Key 无效或已被撤销")
        if response.status_code >= 300:
            raise HTTPException(400, f"添加域名失败（{response.status_code}）")
        return {"ok": True, **response.json()}

    def verify_domain(self, domain_id):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", domain_id):
            raise HTTPException(400, "域名标识无效")
        response = httpx.post(
            f"{RESEND_API}/domains/{domain_id}/verify",
            headers=self._resend_headers(),
            timeout=30,
        )
        if response.status_code == 401:
            raise HTTPException(400, "Resend API Key 无效或已被撤销")
        if response.status_code >= 300:
            raise HTTPException(400, f"验证请求失败（{response.status_code}）")
        return {"ok": True}

    def consume(self, email, scene, code, verified):
        if not self.enabled():
            raise HTTPException(503, "邮箱服务尚未配置，请使用账号密码登录")
        success = False
        with self.store.connect(write=True) as db:
            row = db.execute(
                "SELECT * FROM email_codes WHERE scene=? ORDER BY created DESC LIMIT 1",
                (scene,),
            ).fetchone()
            if (
                row
                and not row["used"]
                and row["expires"] > time.time()
                and row["attempts"] < 5
            ):
                success = hmac.compare_digest(
                    self.digest(email, scene, code), row["digest"]
                ) and hmac.compare_digest(
                    email.encode(),
                    self.auth.secret("owner_email").strip().lower().encode(),
                )
                attempts = row["attempts"] + 1
                db.execute(
                    "UPDATE email_codes SET attempts=?,used=? WHERE id=?",
                    (attempts, int(success or attempts >= 5), row["id"]),
                )
                if success:
                    verified(db)
        # Commit failed attempts before responding; raising inside would roll them back.
        if not success:
            raise HTTPException(400, "验证码不正确、已过期或已使用，请重新获取")
