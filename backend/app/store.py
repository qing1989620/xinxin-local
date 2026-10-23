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
    return clean_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    )


def clean_text(value):
    """把文本修成可安全入库/输出的 UTF-8 字符串。

    PDF 字体抽取、模型 JSON 里的 \\udxxx 转义都可能带出落单的 UTF-16
    代理项；sqlite 按 UTF-8 绑定参数时会直接抛 UnicodeEncodeError。
    策略：成对代理项合成正式码点，落单的替换为 U+FFFD；干净字符串原样返回。
    """
    if isinstance(value, str) and value:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            return value.encode("utf-16", "surrogatepass").decode(
                "utf-16", "replace"
            )
    return value


def _bind(args):
    return [clean_text(arg) if isinstance(arg, str) else arg for arg in args]


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
                CREATE TABLE IF NOT EXISTS music_plays(id TEXT PRIMARY KEY,track_id TEXT NOT NULL,source TEXT NOT NULL,name TEXT NOT NULL,artist TEXT NOT NULL DEFAULT '',album TEXT NOT NULL DEFAULT '',valence REAL NOT NULL,energy REAL NOT NULL,label TEXT NOT NULL,created INTEGER NOT NULL);
                CREATE INDEX IF NOT EXISTS messages_conversation ON messages(conversation_id,created);
                CREATE INDEX IF NOT EXISTS music_plays_created ON music_plays(created);
                CREATE TABLE IF NOT EXISTS music_emotions(track_key TEXT PRIMARY KEY,valence REAL NOT NULL,energy REAL NOT NULL,label TEXT NOT NULL,reason TEXT NOT NULL DEFAULT '',created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS books(id TEXT PRIMARY KEY,file_id TEXT,title TEXT NOT NULL,author TEXT NOT NULL DEFAULT '',subject TEXT NOT NULL DEFAULT '',pages INTEGER NOT NULL DEFAULT 0,char_count INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'ready',created INTEGER NOT NULL,updated INTEGER NOT NULL);
                CREATE INDEX IF NOT EXISTS books_updated ON books(updated);
                CREATE TABLE IF NOT EXISTS book_chapters(id TEXT PRIMARY KEY,book_id TEXT NOT NULL,idx INTEGER NOT NULL,title TEXT NOT NULL,page_from INTEGER,page_to INTEGER,content TEXT NOT NULL DEFAULT '',created INTEGER NOT NULL);
                CREATE INDEX IF NOT EXISTS book_chapters_book ON book_chapters(book_id,idx);
                CREATE TABLE IF NOT EXISTS questions(id TEXT PRIMARY KEY,book_id TEXT,chapter_id TEXT,hash TEXT NOT NULL UNIQUE,kind TEXT NOT NULL,stem TEXT NOT NULL,options TEXT NOT NULL DEFAULT '[]',answer TEXT NOT NULL DEFAULT '',explanation TEXT NOT NULL DEFAULT '',tags TEXT NOT NULL DEFAULT '[]',difficulty INTEGER NOT NULL DEFAULT 2,created INTEGER NOT NULL);
                CREATE INDEX IF NOT EXISTS questions_chapter ON questions(chapter_id);
                CREATE TABLE IF NOT EXISTS learning_sources(id TEXT PRIMARY KEY,book_id TEXT NOT NULL,chapter_id TEXT NOT NULL,idx INTEGER NOT NULL,label TEXT NOT NULL,content TEXT NOT NULL,page_from INTEGER,page_to INTEGER,UNIQUE(chapter_id,idx));
                CREATE INDEX IF NOT EXISTS learning_sources_book ON learning_sources(book_id);
                CREATE TABLE IF NOT EXISTS learning_source_analysis(source_id TEXT PRIMARY KEY,version INTEGER NOT NULL,data TEXT NOT NULL,created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS learning_visual_pages(book_id TEXT NOT NULL,page INTEGER NOT NULL,version INTEGER NOT NULL,model TEXT NOT NULL,data TEXT NOT NULL,created INTEGER NOT NULL,PRIMARY KEY(book_id,page,version,model));
                CREATE TABLE IF NOT EXISTS learning_source_edits(source_id TEXT PRIMARY KEY,edited INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS learning_book_extractions(book_id TEXT PRIMARY KEY,data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS file_extractions(file_id TEXT PRIMARY KEY,data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS file_ocr_pages(file_id TEXT NOT NULL,page INTEGER NOT NULL,text TEXT NOT NULL,uncertain INTEGER NOT NULL DEFAULT 0,version INTEGER NOT NULL,PRIMARY KEY(file_id,page));
                CREATE TABLE IF NOT EXISTS learning_imports(id TEXT PRIMARY KEY,run_id TEXT,file_id TEXT NOT NULL,book_id TEXT,request_key TEXT NOT NULL UNIQUE,signature TEXT NOT NULL,created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS learning_generations(id TEXT PRIMARY KEY,book_id TEXT NOT NULL,run_id TEXT,request_key TEXT NOT NULL UNIQUE,signature TEXT NOT NULL,options TEXT NOT NULL,created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS learning_generation_items(job_id TEXT NOT NULL,source_id TEXT NOT NULL,target INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'pending',created_count INTEGER NOT NULL DEFAULT 0,rejected INTEGER NOT NULL DEFAULT 0,duplicates INTEGER NOT NULL DEFAULT 0,error TEXT NOT NULL DEFAULT '',PRIMARY KEY(job_id,source_id));
                CREATE TABLE IF NOT EXISTS quiz_sessions(id TEXT PRIMARY KEY,book_id TEXT,chapter_id TEXT,title TEXT NOT NULL DEFAULT '',total INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'active',created INTEGER NOT NULL,finished INTEGER);
                CREATE TABLE IF NOT EXISTS quiz_session_questions(session_id TEXT NOT NULL,question_id TEXT NOT NULL,idx INTEGER NOT NULL,PRIMARY KEY(session_id,question_id));
                CREATE TABLE IF NOT EXISTS quiz_answers(id TEXT PRIMARY KEY,session_id TEXT NOT NULL,question_id TEXT NOT NULL,answer TEXT NOT NULL DEFAULT '',status TEXT NOT NULL,grade_method TEXT NOT NULL DEFAULT 'exact',ai_reason TEXT NOT NULL DEFAULT '',created INTEGER NOT NULL);
                CREATE INDEX IF NOT EXISTS quiz_answers_session ON quiz_answers(session_id,created);
                CREATE TABLE IF NOT EXISTS tutor_messages(id TEXT PRIMARY KEY,question_id TEXT NOT NULL,role TEXT NOT NULL,content TEXT NOT NULL,created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS music_favorites(track_key TEXT PRIMARY KEY,track_id TEXT,source TEXT,name TEXT NOT NULL,artist TEXT NOT NULL DEFAULT '',album TEXT NOT NULL DEFAULT '',cover TEXT NOT NULL DEFAULT '',created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS music_playlists(id TEXT PRIMARY KEY,name TEXT NOT NULL,created INTEGER NOT NULL,updated INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS music_playlist_tracks(playlist_id TEXT NOT NULL,track_key TEXT NOT NULL,position INTEGER NOT NULL,track_id TEXT,source TEXT,name TEXT NOT NULL,artist TEXT NOT NULL DEFAULT '',album TEXT NOT NULL DEFAULT '',cover TEXT NOT NULL DEFAULT '',created INTEGER NOT NULL,PRIMARY KEY(playlist_id,track_key));
                CREATE INDEX IF NOT EXISTS tutor_messages_question ON tutor_messages(question_id,created);
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
            if "moods" not in {
                row["name"] for row in db.execute("PRAGMA table_info(music_emotions)")
            }:
                db.execute(
                    "ALTER TABLE music_emotions ADD COLUMN moods TEXT NOT NULL DEFAULT '[]'"
                )
            if "mode" not in {
                row["name"] for row in db.execute("PRAGMA table_info(tutor_messages)")
            }:
                db.execute(
                    "ALTER TABLE tutor_messages ADD COLUMN mode TEXT NOT NULL DEFAULT 'teacher'"
                )
            for column, declaration in {
                "source_id": "TEXT",
                "source_quote": "TEXT NOT NULL DEFAULT ''",
                "origin": "TEXT NOT NULL DEFAULT 'legacy'",
                "review": "TEXT NOT NULL DEFAULT 'legacy'",
                "generation_id": "TEXT",
                "source_pages": "TEXT NOT NULL DEFAULT '[]'",
                "source_method": "TEXT NOT NULL DEFAULT 'text'",
            }.items():
                if column not in {row["name"] for row in db.execute("PRAGMA table_info(questions)")}:
                    db.execute(f"ALTER TABLE questions ADD COLUMN {column} {declaration}")
            if "mode" not in {row["name"] for row in db.execute("PRAGMA table_info(quiz_sessions)")}:
                db.execute("ALTER TABLE quiz_sessions ADD COLUMN mode TEXT NOT NULL DEFAULT 'all'")
            db.execute("CREATE INDEX IF NOT EXISTS questions_source ON questions(source_id)")
            if "attempt_seq" not in {row["name"] for row in db.execute("PRAGMA table_info(quiz_answers)")}:
                db.execute("ALTER TABLE quiz_answers ADD COLUMN attempt_seq INTEGER NOT NULL DEFAULT 0")
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
    def connect(self, write=False):
        # WAL cleanup races on Windows: a connection opened while the WAL/shm
        # is being (re)created can be treated as readonly (SQLITE_READONLY, not
        # SQLITE_BUSY). Retry the write lock on a fresh connection *before*
        # yielding, so callers never re-run their body after side effects.
        db = self._open()
        if write:
            for attempt in range(8):
                try:
                    db.execute("BEGIN IMMEDIATE")
                    break
                except sqlite3.OperationalError as exc:
                    message = str(exc).lower()
                    if "readonly" not in message and "locked" not in message:
                        raise
                    db.close()
                    time.sleep(0.01 * (attempt + 1))
                    db = self._open()
            else:
                raise sqlite3.OperationalError("无法获取数据库写锁")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _open(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=15000")
        # Touch the schema page so the WAL/shm is attached before any write.
        db.execute("SELECT count(*) FROM sqlite_master").fetchone()
        return db

    def all(self, sql, args=()):
        with self.connect() as db:
            return [
                dict(row) for row in db.execute(sql, _bind(args)).fetchall()
            ]

    def one(self, sql, args=()):
        rows = self.all(sql, args)
        return rows[0] if rows else None

    def execute(self, sql, args=()):
        # Single-statement writes still need the same WAL race retry as
        # connect(write=True): a readonly error means the statement never ran,
        # so replaying it is safe (the failed transaction was rolled back).
        for attempt in range(5):
            try:
                with self.connect(write=True) as db:
                    return db.execute(sql, _bind(args)).rowcount
            except sqlite3.OperationalError as exc:
                message = str(exc).lower()
                if attempt == 4 or (
                    "readonly" not in message and "locked" not in message
                ):
                    raise
                time.sleep(0.02 * (attempt + 1))

    def setting(self, key, default=None):
        row = self.one("SELECT value FROM settings WHERE key=?", (key,))
        return json.loads(row["value"]) if row else default

    def set_setting(self, key, value):
        self.execute(
            "INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, encode(value)),
        )

    def event(self, run_id, kind, data):
        with self.connect(write=True) as db:
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
