"""Explicit, local-only migration. Never imports accounts, secrets or sessions."""

import argparse
import json
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import Config
from app.files import FileLibrary
from app.store import Store, encode, now

TABLES = (
    "Article",
    "Collection",
    "Photo",
    "Poem",
    "ResumeProfile",
    "ResumeSkill",
    "ResumeExperience",
)


def migrate(source: Path, store: Store, namespace="myself", apply=False):
    source = source.resolve()
    db = sqlite3.connect((source / "dev.db").as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    tables = {
        row[0]
        for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    rows = {
        table: (
            [dict(row) for row in db.execute(f'SELECT * FROM "{table}"')]
            if table in tables
            else []
        )
        for table in TABLES
    }
    summary = {
        "mode": "apply" if apply else "dry-run",
        "source_counts": {k: len(v) for k, v in rows.items()},
        "records_added": 0,
        "files_added": 0,
        "unresolved_assets": 0,
    }
    if not apply:
        db.close()
        return summary
    library = FileLibrary(store)
    public = (source / "public").resolve()

    def ident(table, key):
        return uuid.uuid5(uuid.NAMESPACE_URL, f"xinxin:{namespace}:{table}:{key}").hex

    def asset(value):
        if not value or not isinstance(value, str):
            return None
        parsed = urlsplit(value)
        # External images are not fetched or sent elsewhere by migration.
        if parsed.scheme or parsed.netloc:
            return None
        relative = unquote(parsed.path).lstrip("/")
        cache_key = "migration-file:" + ident("asset", relative)
        saved = store.setting(cache_key)
        if saved and store.one("SELECT id FROM files WHERE id=?", (saved,)):
            return saved
        target = (public / relative).resolve()
        data, mime = None, None
        if target.is_relative_to(public) and target.is_file():
            data = target.read_bytes()
        elif relative.startswith("api/images/") and "StoredImage" in tables:
            image = db.execute(
                "SELECT data,mimeType FROM StoredImage WHERE filename=?",
                (Path(relative).name,),
            ).fetchone()
            if image:
                data, mime = bytes(image["data"]), image["mimeType"]
        if data:
            saved = library.save(Path(relative).name, data, mime)["id"]
            store.set_setting(cache_key, saved)
            summary["files_added"] += 1
            return saved
        summary["unresolved_assets"] += 1
        return None

    def image_nodes(node):
        if isinstance(node, list):
            return [image_nodes(item) for item in node]
        if not isinstance(node, dict):
            return node
        node = {k: image_nodes(v) for k, v in node.items()}
        if node.get("type") == "image":
            attrs = node.setdefault("attrs", {})
            file_id = asset(attrs.get("src"))
            if file_id:
                attrs["file_id"] = file_id
                attrs["src"] = ""
        return node

    def timestamp(value):
        if isinstance(value, (int, float)):
            return int(value)
        try:
            return int(
                datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
                * 1000
            )
        except (ValueError, TypeError):
            return now()

    def save(kind, table, row, payload):
        record_id = ident(table, row["id"])
        if store.one("SELECT id FROM records WHERE id=?", (record_id,)):
            return
        payload["legacy"] = {"project": namespace, "table": table, "id": row["id"]}
        store.execute(
            "INSERT INTO records VALUES(?,?,?,?,?)",
            (
                record_id,
                kind,
                encode(payload),
                timestamp(row.get("createdAt")),
                timestamp(row.get("updatedAt")),
            ),
        )
        summary["records_added"] += 1

    for row in rows["Collection"]:
        payload = {
            k: v for k, v in row.items() if k not in {"id", "createdAt", "updatedAt"}
        }
        payload["title"] = row["name"]
        payload["cover_file_id"] = asset(row.get("coverImage"))
        save("collection", "Collection", row, payload)
    for row in rows["Article"]:
        payload = {
            k: v
            for k, v in row.items()
            if k not in {"id", "createdAt", "updatedAt", "authorId", "collectionId"}
        }
        try:
            payload["content"] = encode(image_nodes(json.loads(row["content"])))
        except (ValueError, TypeError):
            pass
        payload["collection_id"] = (
            ident("Collection", row["collectionId"]) if row.get("collectionId") else ""
        )
        payload["cover_file_id"] = asset(row.get("coverImage"))
        save("article", "Article", row, payload)
    for row in rows["Photo"]:
        payload = {
            k: v
            for k, v in row.items()
            if k not in {"id", "createdAt", "updatedAt", "authorId"}
        }
        payload["file_id"] = asset(row.get("url"))
        save("photo", "Photo", row, payload)
    for row in rows["Poem"]:
        save(
            "poem",
            "Poem",
            row,
            {
                k: v
                for k, v in row.items()
                if k not in {"id", "createdAt", "updatedAt", "authorId"}
            },
        )
    for row in rows["ResumeProfile"]:
        payload = {
            k: v for k, v in row.items() if k not in {"id", "createdAt", "updatedAt"}
        }
        payload["avatar_file_id"] = asset(row.get("avatar"))
        payload["pdf_file_id"] = asset(row.get("resumePdf"))
        payload["skills"] = [
            {k: v for k, v in item.items() if k not in {"id", "profileId"}}
            for item in rows["ResumeSkill"]
            if item["profileId"] == row["id"]
        ]
        payload.update(education=[], experiences=[], certificates=[])
        for item in sorted(
            rows["ResumeExperience"], key=lambda item: item.get("sortOrder", 0)
        ):
            if item["profileId"] != row["id"]:
                continue
            entry = {k: v for k, v in item.items() if k not in {"id", "profileId"}}
            entry["image_file_id"] = asset(item.get("image"))
            section = (
                "education"
                if item["type"] == "education"
                else (
                    "certificates"
                    if item["type"] in {"certificate", "competition"}
                    else "experiences"
                )
            )
            payload[section].append(entry)
        save("resume", "ResumeProfile", row, payload)
    db.close()
    store.audit("migration.myself", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Explicit checkout/export directory containing dev.db and public/",
    )
    parser.add_argument("--namespace", default="myself")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Import content into ignored local data; existing imported records are retained",
    )
    args = parser.parse_args()
    print(
        json.dumps(
            migrate(
                args.source,
                Store(Config.from_env().data_dir),
                args.namespace,
                args.apply,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )
