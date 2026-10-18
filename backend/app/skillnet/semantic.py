"""SkillNet's pinned E5 encoder adapted to Xinxin's private data directory.

Source: skillnet-demo 0af2de6, skillnet/semantic.py + model_assets.py.
Pooling, normalization, prefixes and routing weights follow that implementation.
No model downloads occur on the request path. Model weights stay outside Git.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from pathlib import Path
from zipfile import BadZipFile

from .index import VectorIndex

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "resources/semantic/model.json"
WEIGHTS = (0.70, 0.20, 0.10)
DENSE_WEIGHTS = (0.35, 0.55, 0.10)


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def verify_model(directory: Path) -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for name, info in manifest["files"].items():
        path = directory / name
        if path.stat().st_size != info["bytes"] or digest(path) != info["sha256"]:
            raise ValueError("Semantic model integrity check failed")
    return manifest


class DenseIndex:
    def __init__(self, model_dir: Path, cache_dir: Path):
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer

        manifest = verify_model(model_dir)
        self.np, self.cache_dir = np, cache_dir
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.session = ort.InferenceSession(
            str(model_dir / "onnx/model_quantized.onnx"),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
        self.tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=256)
        self.tokenizer.enable_padding()
        self.lock = threading.Lock()
        self.snapshot = ([], np.empty((0, 384), dtype=np.float32))
        self.status = {
            "kind": "dense-onnx",
            "active": True,
            "degraded": False,
            "model": manifest["repository"],
            "revision": manifest["revision"],
            "dimension": 384,
            "max_tokens": 256,
            "threads": 2,
        }
        # Some native runtimes fail only on the first inference, not session load.
        # Warm up inside the factory's guarded initialization boundary.
        self.embed(["semantic readiness check"], "query: ")

    def embed(self, texts: list[str], prefix: str):
        np, matrices = self.np, []
        with self.lock:
            for start in range(0, len(texts), 8):
                tokens = self.tokenizer.encode_batch(
                    [prefix + t for t in texts[start : start + 8]]
                )
                arrays = {
                    "input_ids": np.array([t.ids for t in tokens], dtype=np.int64),
                    "attention_mask": np.array(
                        [t.attention_mask for t in tokens], dtype=np.int64
                    ),
                    "token_type_ids": np.array(
                        [t.type_ids for t in tokens], dtype=np.int64
                    ),
                }
                output = self.session.run(
                    None, {i.name: arrays[i.name] for i in self.session.get_inputs()}
                )[0]
                mask = arrays["attention_mask"][..., None]
                pooled = (output * mask).sum(axis=1) / mask.sum(axis=1).clip(min=1)
                pooled /= np.linalg.norm(pooled, axis=1, keepdims=True).clip(min=1e-12)
                matrices.append(pooled.astype(np.float32))
        return (
            np.concatenate(matrices)
            if matrices
            else np.empty((0, 384), dtype=np.float32)
        )

    def fit(self, ids: list[str], texts: list[str]):
        key = hashlib.sha256(
            json.dumps(
                [self.status["revision"], 256, ids, texts], ensure_ascii=False
            ).encode()
        ).hexdigest()
        cache = self.cache_dir / (key + ".npz")
        matrix = None
        if cache.is_file():
            try:
                with self.np.load(cache, allow_pickle=False) as data:
                    candidate = data["embeddings"]
                if (
                    candidate.shape == (len(ids), 384)
                    and candidate.dtype == self.np.float32
                    and self.np.isfinite(candidate).all()
                    and self.np.allclose(
                        self.np.linalg.norm(candidate, axis=1), 1, atol=1e-4
                    )
                ):
                    matrix = candidate
            except (OSError, ValueError, KeyError, EOFError, BadZipFile):
                pass
        if matrix is None:
            matrix = self.embed(texts, "passage: ")
            temporary = cache.with_name(key + "-" + uuid.uuid4().hex + ".tmp.npz")
            try:
                cache.parent.mkdir(parents=True, exist_ok=True)
                self.np.savez_compressed(temporary, embeddings=matrix)
                temporary.replace(cache)
            except OSError:
                pass  # Optional cache; a busy disk must not break in-memory routing.
            finally:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
        self.snapshot = (list(ids), matrix)

    def search(self, query: str, top_k: int = 20):
        ids, matrix = self.snapshot
        if not ids or not query.strip():
            return []
        scores = matrix @ self.embed([query], "query: ")[0]
        order = self.np.argsort(-scores)[:top_k]
        return [(ids[i], round(float(scores[i]), 5)) for i in order]


def make_index(data_dir: Path):
    mode = os.getenv("XINXIN_SKILL_ENCODER", "auto")
    if mode not in {"auto", "dense", "lexical"}:
        raise ValueError("XINXIN_SKILL_ENCODER must be auto, dense or lexical")
    directory = data_dir / "semantic-model"
    reason = "已选择轻量词法模式"
    if mode != "lexical":
        try:
            return DenseIndex(directory, data_dir / "semantic-cache")
        except Exception:
            # Native ORT Fail/RuntimeException/NotImplemented are not Python
            # RuntimeError subclasses. This is the optional encoder boundary;
            # auto must degrade for any initialization failure, dense must fail.
            # Never expose local paths, exception inputs or an opaque model error.
            reason = "语义模型或推理依赖不可用；请运行 scripts/setup_semantic_model.py 并重启后端"
    if mode == "dense":
        raise RuntimeError(reason)
    index = VectorIndex()
    index.status = {
        "kind": "lexical-hashing",
        "active": True,
        "degraded": mode != "lexical",
        "reason": reason,
    }
    return index
