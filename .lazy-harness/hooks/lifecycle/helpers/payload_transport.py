"""Lossless lifecycle payload transport; callers own referenced-file lifetime."""
from pathlib import Path


def read_payload_text(raw: str) -> str:
    """Accept legacy inline JSON or an explicit @file: reference, without fallback."""
    if not raw.startswith("@file:"):
        return raw
    path = raw[6:]
    if not path:
        raise ValueError("empty lifecycle payload reference")
    return Path(path).read_text(encoding="utf-8")
