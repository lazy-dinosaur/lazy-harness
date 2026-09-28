"""Pinned, offline E5 embeddings; model files + venv live in knowledge.json embed.model_dir (v2 namespace)."""
import hashlib
import json
import os
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

MODEL_ID = "intfloat/multilingual-e5-small@614241f622f53c4eeff9890bdc4f31cfecc418b3"
# Model + venv location comes from knowledge.json embed.model_dir (default ~/.local/share/lazy-harness-v2/e5-small).
def _model_dir():
    try:
        import config
        return Path(config.load()["embed_model_dir"])
    except Exception:  # config errors must not hide the pinned-hash check below
        return Path(os.environ.get("LH_EMBED_MODEL_DIR") or Path.home() / ".local/share/lazy-harness-v2/e5-small")


_MODEL_DIR = _model_dir()
_PINS = {"model.onnx": "ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665",
         "tokenizer.json": "0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39"}


def _verify():
    for name, expected in _PINS.items():
        digest = hashlib.sha256()
        with (_MODEL_DIR / name).open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != expected:
            raise RuntimeError(f"E5 {name} SHA256 mismatch")


def _infer(texts, role):
    import numpy as np
    import onnxruntime as ort
    from tokenizers import Tokenizer

    _verify()
    tokenizer = Tokenizer.from_file(str(_MODEL_DIR / "tokenizer.json"))
    tokenizer.enable_padding(pad_id=1, pad_token="<pad>")
    encodings = tokenizer.encode_batch([role + ": " + text for text in texts])
    if any(len(item.ids) > 512 for item in encodings):
        raise ValueError("E5 input exceeds 512 tokens; truncation forbidden")
    arrays = {"input_ids": np.asarray([e.ids for e in encodings], dtype=np.int64),
              "attention_mask": np.asarray([e.attention_mask for e in encodings], dtype=np.int64),
              "token_type_ids": np.asarray([e.type_ids for e in encodings], dtype=np.int64)}
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    session = ort.InferenceSession(str(_MODEL_DIR / "model.onnx"), sess_options=options,
                                   providers=["CPUExecutionProvider"])
    hidden = session.run(None, {item.name: arrays[item.name] for item in session.get_inputs()})[0]
    if hidden.ndim != 3 or hidden.shape[2] != 384:
        raise RuntimeError("unexpected E5 output dimensions")
    mask = arrays["attention_mask"][..., None].astype(np.float32)
    pooled = (hidden * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1)
    vectors = pooled / np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12)
    if not np.isfinite(vectors).all() or not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5):
        raise RuntimeError("invalid E5 vector")
    return vectors.tolist()


class EmbeddingUnavailable(RuntimeError):
    pass


def _encode(texts, role):
    if not texts:
        return []
    if not all(isinstance(text, str) for text in texts):
        raise ValueError("E5 inputs must be strings")
    request = urllib.request.Request(
        os.environ.get("LH_EMBED_URL", "http://127.0.0.1:8765").rstrip("/") + "/embed",
        data=json.dumps({"texts": texts, "role": role}).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        if isinstance(error, urllib.error.HTTPError):
            raise ValueError(error.read().decode("utf-8")) from error
        raise EmbeddingUnavailable("local embedding service unavailable") from error
    if result.get("model_id") != MODEL_ID:
        raise RuntimeError("embedding model_id mismatch")
    return result["vectors"]


def encode_passages(texts):
    return [vector for start in range(0, len(texts), 64)
            for vector in _encode(texts[start:start + 64], "passage")]


@lru_cache(maxsize=128)
def encode_query(text):
    return _encode([text], "query")[0]


