from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import threading
import time

from cryptography.fernet import Fernet
from fastapi import HTTPException


def password_hash(password: str):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return base64.b64encode(salt + digest).decode()


def password_matches(password, stored):
    try:
        raw = base64.b64decode(stored)
        digest = hashlib.scrypt(password.encode(), salt=raw[:16], n=16384, r=8, p=1)
        return hmac.compare_digest(raw[16:], digest)
    except (ValueError, TypeError):
        return False


class Auth:
    def __init__(self, store):
        self.store = store
        self.lock = threading.Lock()
        self.failures = {}
        key_path = store.directory / "vault.key"
        if not key_path.exists():
            key_path.write_bytes(Fernet.generate_key())
            try:
                key_path.chmod(0o600)
            except OSError:
                pass
        self.vault = Fernet(key_path.read_bytes())

    def secret(self, key, default=""):
        encrypted = self.store.setting("secret:" + key)
        return self.vault.decrypt(encrypted.encode()).decode() if encrypted else default

    def set_secret(self, key, value):
        self.store.set_setting(
            "secret:" + key, self.vault.encrypt(value.encode()).decode()
        )

    def issue(self):
        token = secrets.token_urlsafe(40)
        self.store.execute("DELETE FROM sessions WHERE expires<?", (time.time(),))
        self.store.execute(
            "INSERT INTO sessions VALUES(?,?)",
            (hashlib.sha256(token.encode()).hexdigest(), time.time() + 30 * 86400),
        )
        return token

    def require(self, authorization):
        token = (authorization or "").removeprefix("Bearer ")
        row = self.store.one(
            "SELECT expires FROM sessions WHERE hash=?",
            (hashlib.sha256(token.encode()).hexdigest(),),
        )
        if not token or not row or row["expires"] <= time.time():
            raise HTTPException(401, "会话已失效，请登录")
        return token

    def login(self, name, password, peer):
        with self.lock:
            recent = [t for t in self.failures.get(peer, []) if t > time.time() - 900]
            if len(recent) >= 8:
                raise HTTPException(429, "尝试过于频繁，请稍后再试")
            owner = self.store.one("SELECT * FROM owner WHERE id=1")
            if (
                not owner
                or not hmac.compare_digest(name.encode(), owner["name"].encode())
                or not password_matches(password, owner["password"])
            ):
                self.failures[peer] = recent + [time.time()]
                raise HTTPException(401, "账号或密码不正确")
            self.failures.pop(peer, None)
        return self.issue()
