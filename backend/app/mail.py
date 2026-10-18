"""Single-owner email codes. No registration and no plaintext codes at rest.

Adapted design: lankhub email/verify-code.ts (MIT), pinned in THIRD_PARTY.md.
The sender here uses TLS SMTP instead of lankhub's Resend transport.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import smtplib
import ssl
import time
from email.message import EmailMessage

from fastapi import HTTPException

from .store import uid


class MailCodes:
    def __init__(self, store, auth):
        self.store, self.auth = store, auth
        key = auth.secret("email_hmac_key")
        if not key:
            key = secrets.token_hex(32)
            auth.set_secret("email_hmac_key", key)
        self.key = key.encode()
        with store.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS email_codes(
                id TEXT PRIMARY KEY, scene TEXT NOT NULL, digest TEXT NOT NULL,
                expires REAL NOT NULL, created REAL NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                used INTEGER NOT NULL DEFAULT 0, peer_hash TEXT NOT NULL)""")
            db.execute(
                "CREATE INDEX IF NOT EXISTS email_codes_created ON email_codes(created)"
            )

    def enabled(self):
        config = self.configuration()
        return bool(
            config["email"]
            and config["smtp_password"]
            and self.store.one("SELECT id FROM owner")
        )

    def configuration(self):
        # A single SELECT observes one committed set of TLS and credentials.
        rows = {
            row["key"]: json.loads(row["value"])
            for row in self.store.all(
                "SELECT key,value FROM settings WHERE key IN ('secret:owner_email','secret:smtp_username','secret:smtp_password','smtp_host','smtp_port','smtp_mode')"
            )
        }

        def secret(name):
            value = rows.get("secret:" + name)
            return self.auth.vault.decrypt(value.encode()).decode() if value else ""

        email = secret("owner_email")
        return {
            "email": email,
            "smtp_username": secret("smtp_username") or email,
            "smtp_password": secret("smtp_password"),
            "smtp_host": rows.get("smtp_host", "smtp.qq.com"),
            "smtp_port": rows.get("smtp_port", 465),
            "smtp_mode": rows.get("smtp_mode", "ssl"),
        }

    def configure(self, values):
        email = values["email"].strip().lower()
        plain = {key: values[key] for key in ("smtp_host", "smtp_port", "smtp_mode")}
        to_save = {
            "owner_email": email,
            "smtp_username": values["smtp_username"] or email,
        }
        if values["smtp_password"]:
            to_save["smtp_password"] = values["smtp_password"]
        encrypted = {
            "secret:" + key: self.auth.vault.encrypt(value.encode()).decode()
            for key, value in to_save.items()
        }
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
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
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
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
        except Exception:
            self.store.execute("UPDATE email_codes SET used=1 WHERE id=?", (ident,))
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
        host, port, username, mode, password = (
            config[key]
            for key in (
                "smtp_host",
                "smtp_port",
                "smtp_username",
                "smtp_mode",
                "smtp_password",
            )
        )
        message = EmailMessage()
        message["From"] = username
        message["To"] = recipient
        message["Subject"] = "Xinxin · " + (
            "登录验证码" if scene == "login" else "重置密码验证码"
        )
        message.set_content(
            f'你的 Xinxin 验证码是：{code}\n\n此验证码 10 分钟内有效，仅可使用一次。\n用途：{"登录" if scene == "login" else "重置密码"}。\n如果这次操作不是你发起的，请忽略此邮件。'
        )
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

    def consume(self, email, scene, code, verified):
        if not self.enabled():
            raise HTTPException(503, "邮箱服务尚未配置，请使用账号密码登录")
        success = False
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
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
