from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path


def uid():
    return uuid.uuid4().hex


def now():
    return int(time.time() * 1000)


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class Store:
    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "xinxin.sqlite3"
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS owner(id INTEGER PRIMARY KEY CHECK(id=1),name TEXT NOT NULL,password TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions(hash TEXT PRIMARY KEY,expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY,title TEXT NOT NULL,created INTEGER NOT NULL,updated INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL,role TEXT NOT NULL,content TEXT NOT NULL,created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL,task TEXT NOT NULL,status TEXT NOT NULL,permission TEXT NOT NULL,server_id TEXT,max_calls INTEGER NOT NULL,max_seconds INTEGER NOT NULL,created INTEGER NOT NULL,updated INTEGER NOT NULL,result TEXT NOT NULL DEFAULT '',error TEXT NOT NULL DEFAULT '',usage TEXT NOT NULL DEFAULT '{}',request_key TEXT UNIQUE);
                CREATE TABLE IF NOT EXISTS events(run_id TEXT NOT NULL,seq INTEGER NOT NULL,kind TEXT NOT NULL,data TEXT NOT NULL,created INTEGER NOT NULL,PRIMARY KEY(run_id,seq));
                CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY,kind TEXT NOT NULL,payload TEXT NOT NULL,created INTEGER NOT NULL,updated INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS files(id TEXT PRIMARY KEY,name TEXT NOT NULL,mime TEXT NOT NULL,size INTEGER NOT NULL,sha256 TEXT NOT NULL,path TEXT NOT NULL,text TEXT NOT NULL DEFAULT '',run_id TEXT,created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS uploads(request_id TEXT PRIMARY KEY,file_id TEXT NOT NULL,signature TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS memories(id TEXT PRIMARY KEY,content TEXT NOT NULL,category TEXT NOT NULL,created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS schedules(id TEXT PRIMARY KEY,title TEXT NOT NULL,task TEXT NOT NULL,interval_minutes INTEGER NOT NULL,next_at INTEGER NOT NULL,enabled INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE IF NOT EXISTS audit(id TEXT PRIMARY KEY,action TEXT NOT NULL,data TEXT NOT NULL,created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS run_context(run_id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL,messages TEXT NOT NULL,message_cursor INTEGER NOT NULL,updated INTEGER NOT NULL);
                CREATE INDEX IF NOT EXISTS context_conversation ON run_context(conversation_id,updated);
                CREATE TABLE IF NOT EXISTS run_plan(run_id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL,steps TEXT NOT NULL,updated INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS message_runs(message_id TEXT PRIMARY KEY,run_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS conversation_options(conversation_id TEXT PRIMARY KEY,context_window_tokens INTEGER NOT NULL);
                CREATE INDEX IF NOT EXISTS messages_conversation ON messages(conversation_id,created);
                CREATE INDEX IF NOT EXISTS records_kind ON records(kind,updated);
                CREATE INDEX IF NOT EXISTS runs_created ON runs(created);
            """)
            schedule_columns = {
                row["name"] for row in db.execute("PRAGMA table_info(schedules)")
            }
            if "permission" not in schedule_columns:
                db.execute(
                    "ALTER TABLE schedules ADD COLUMN permission TEXT NOT NULL DEFAULT 'read'"
                )
            if "server_id" not in schedule_columns:
                db.execute("ALTER TABLE schedules ADD COLUMN server_id TEXT")
            if "request_signature" not in {
                row["name"] for row in db.execute("PRAGMA table_info(runs)")
            }:
                db.execute(
                    "ALTER TABLE runs ADD COLUMN request_signature TEXT NOT NULL DEFAULT ''"
                )
            db.execute(
                "UPDATE runs SET status='interrupted',error='服务重启，任务已中断；未自动重跑。',updated=? WHERE status IN ('queued','running','cancelling')",
                (now(),),
            )
            if "allow_memory" not in {
                row["name"] for row in db.execute("PRAGMA table_info(runs)")
            }:
                db.execute(
                    "ALTER TABLE runs ADD COLUMN allow_memory INTEGER NOT NULL DEFAULT 0"
                )
            if "max_total_tokens" not in {
                row["name"] for row in db.execute("PRAGMA table_info(runs)")
            }:
                db.execute(
                    "ALTER TABLE runs ADD COLUMN max_total_tokens INTEGER NOT NULL DEFAULT 50000"
                )
            if "context_window_tokens" not in {
                row["name"] for row in db.execute("PRAGMA table_info(runs)")
            }:
                db.execute("ALTER TABLE runs ADD COLUMN context_window_tokens INTEGER")
            if "resume_of" not in {
                row["name"] for row in db.execute("PRAGMA table_info(runs)")
            }:
                db.execute("ALTER TABLE runs ADD COLUMN resume_of TEXT")
            if "archived" not in {
                row["name"] for row in db.execute("PRAGMA table_info(conversations)")
            }:
                db.execute(
                    "ALTER TABLE conversations ADD COLUMN archived INTEGER NOT NULL DEFAULT 0"
                )
            # Expired occurrences belong to the downtime, not to this startup.
            db.execute(
                "UPDATE schedules SET next_at=?+interval_minutes*60000 WHERE next_at<=?",
                (now(), now()),
            )

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=15000")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def all(self, sql, args=()):
        with self.connect() as db:
            return [dict(row) for row in db.execute(sql, args).fetchall()]

    def one(self, sql, args=()):
        rows = self.all(sql, args)
        return rows[0] if rows else None

    def execute(self, sql, args=()):
        with self.connect() as db:
            return db.execute(sql, args).rowcount

    def setting(self, key, default=None):
        row = self.one("SELECT value FROM settings WHERE key=?", (key,))
        return json.loads(row["value"]) if row else default

    def set_setting(self, key, value):
        self.execute(
            "INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, encode(value)),
        )

    def event(self, run_id, kind, data):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            seq = db.execute(
                "SELECT COALESCE(MAX(seq),0)+1 FROM events WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            db.execute(
                "INSERT INTO events VALUES(?,?,?,?,?)",
                (run_id, seq, kind, encode(data), now()),
            )
        return seq

    def events(self, run_id, after=0):
        return [
            {**row, "data": json.loads(row["data"])}
            for row in self.all(
                "SELECT * FROM events WHERE run_id=? AND seq>? ORDER BY seq LIMIT 500",
                (run_id, after),
            )
        ]

    def audit(self, action, data):
        self.execute(
            "INSERT INTO audit VALUES(?,?,?,?)", (uid(), action, encode(data), now())
        )

    def message(self, conversation_id, role, content, run_id=None):
        ident = uid()
        self.execute(
            "INSERT INTO messages VALUES(?,?,?,?,?)",
            (ident, conversation_id, role, content, now()),
        )
        self.execute(
            "UPDATE conversations SET updated=? WHERE id=?", (now(), conversation_id)
        )
        if run_id:
            self.execute("INSERT INTO message_runs VALUES(?,?)", (ident, run_id))
        return ident
