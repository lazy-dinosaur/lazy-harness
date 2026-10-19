#!/usr/bin/env python3
"""CURRENT V1 immutable-bundle candidate importer.

Local-first, file-backed importer for a user-authorized frozen V1 export bundle.
It validates the whole manifest and every object before writing any ingestion
artifact. It never writes the V2 DB, never promotes facts, and never treats a
captured source as verified truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

SCHEMA_VERSION = "current-v1-candidate-ingestion/v1"
EXPORT_SCHEMA_VERSION = "v2-current-v1-export/v1"
ACTUAL_EXPORT_SCHEMA_VERSION = "medivance-v1-source-capture-manifest/1.0"
DELTA_EXPORT_SCHEMA_VERSION = "medivance-v1-heldunsupported-delta-manifest/1.0"
SUPPORTED_TEXT_SUFFIXES = {".md", ".markdown", ".mdx", ".txt", ".xml", ".json", ".jsonl", ".html", ".htm", ".tsv", ".csv", ".patch", ".diff"}
DELTA_STRUCTURE_READY = "supported-safe-textcaptured+structure-ready"
DELTA_TERMINAL_DISPOSITIONS = {"linkage-only/notknowledge", "requires-tool", "needs-human/private-excluded", "safety-excluded"}
PRIVATE_PARTS = {".git", ".lazy-harness", ".jcode", "node_modules", "dist", "build", "out", "coverage", ".next", ".turbo", ".cache", "__pycache__"}
PRIVATE_NAMES = {".env", ".env.local", "dsn.local"}
MAX_OBJECT_BYTES = 200 * 1024 * 1024
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
CAPTURED_DISPOSITIONS = {"captured", "captured_needs_review"}


class ImportErrorWithCode(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{sha256_bytes(canonical_json(parts).encode('utf-8'))[:24]}"


def inside(root: Path, child: Path) -> bool:
    try:
        child.relative_to(root)
        return True
    except ValueError:
        return False


def normalize_rel(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ImportErrorWithCode("invalid_path", f"{field} must be a nonempty string")
    if "\x00" in value or "\\" in value:
        raise ImportErrorWithCode("invalid_path", f"{field} contains an invalid character")
    p = Path(value)
    if p.is_absolute():
        raise ImportErrorWithCode("absolute_path", f"{field} must be relative")
    parts = []
    for part in p.parts:
        if part in ("", "."):
            continue
        if part == "..":
            raise ImportErrorWithCode("path_escape", f"{field} escapes its root")
        parts.append(part)
    if not parts:
        raise ImportErrorWithCode("invalid_path", f"{field} is empty after normalization")
    return "/".join(parts)


def private_reason(rel: str) -> str | None:
    parts = rel.split("/")
    if parts[-1] in PRIVATE_NAMES:
        return "private-name-excluded"
    if any(part in PRIVATE_PARTS for part in parts):
        return "private-scope-excluded"
    if any(part.lower().endswith((".pem", ".key", ".p12", ".sqlite", ".db")) for part in parts):
        return "private-binary-or-secret-excluded"
    if any(part.startswith(".") and part not in (".", "..") for part in parts[:-1]):
        return "hidden-directory-excluded"
    return None


@dataclass(frozen=True)
class BundleObject:
    manifest_index: int
    object_path: str
    original_relative_path: str
    source_group: str
    sha256: str
    bytes_count: int
    media_type: str | None
    source_role: str | None
    capture_time: str | None
    body: bytes
    disposition: str = "captured"
    source_kind: str | None = None
    ownership: str | None = None
    reason: str | None = None


def _read_json_file(root: Path, rel: str, expected_sha256: str | None = None) -> dict[str, Any]:
    rel_norm = normalize_rel(rel, rel)
    unresolved = root / rel_norm
    if unresolved.is_symlink():
        raise ImportErrorWithCode("sidecar_path_invalid", f"{rel} is outside the bundle or is not a file")
    path = unresolved.resolve(strict=True)
    if not inside(root, path) or not path.is_file():
        raise ImportErrorWithCode("sidecar_path_invalid", f"{rel} is outside the bundle or is not a file")
    data = path.read_bytes()
    if expected_sha256 and sha256_bytes(data) != expected_sha256:
        raise ImportErrorWithCode("sidecar_hash_mismatch", f"{rel} sha256 mismatch")
    try:
        decoded = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImportErrorWithCode("sidecar_invalid", f"{rel} is not valid UTF-8 JSON") from exc
    if not isinstance(decoded, dict):
        raise ImportErrorWithCode("sidecar_invalid", f"{rel} must contain a JSON object")
    return decoded


def _validate_object(root: Path, index: int, object_path: str, expected_sha: str, expected_bytes: int) -> bytes:
    object_path = normalize_rel(object_path, f"objects.{index}.objectPath")
    if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise ImportErrorWithCode("object_hash_invalid", f"objects.{index}.sha256 invalid")
    if not isinstance(expected_bytes, int) or expected_bytes < 0 or expected_bytes > MAX_OBJECT_BYTES:
        raise ImportErrorWithCode("object_bytes_invalid", f"objects.{index}.bytes invalid")
    unresolved_obj_path = root / object_path
    if unresolved_obj_path.is_symlink():
        raise ImportErrorWithCode("object_path_invalid", f"objects.{index}.objectPath escapes root, is symlink, or is not a file")
    obj_path = unresolved_obj_path.resolve(strict=True)
    if not inside(root, obj_path) or not obj_path.is_file():
        raise ImportErrorWithCode("object_path_invalid", f"objects.{index}.objectPath escapes root, is symlink, or is not a file")
    body = obj_path.read_bytes()
    if len(body) != expected_bytes:
        raise ImportErrorWithCode("object_bytes_mismatch", f"objects.{index}.bytes mismatch")
    if sha256_bytes(body) != expected_sha:
        raise ImportErrorWithCode("object_hash_mismatch", f"objects.{index}.sha256 mismatch")
    return body


def _source_identity(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schemaVersion") == ACTUAL_EXPORT_SCHEMA_VERSION:
        return {"namespace": manifest.get("namespace", "current-v1"), "sourceRoot": manifest.get("root"),
                "sourceGroup": "current-v1", "captureTime": manifest.get("createdAt"),
                "authority": manifest.get("authority"), "stats": manifest.get("stats")}
    identity = manifest.get("sourceIdentity")
    return identity if isinstance(identity, dict) else {}


def _load_actual_manifest(root: Path, manifest: dict[str, Any], manifest_sha: str,
                          expected_source_root: str | None, expected_namespace: str | None,
                          expected_version: str | None) -> tuple[dict[str, Any], list[BundleObject]]:
    version = manifest.get("captureVersion")
    if not isinstance(version, str) or not version.strip():
        raise ImportErrorWithCode("manifest_version_invalid", "captureVersion is required")
    if expected_version and version != expected_version:
        raise ImportErrorWithCode("version_mismatch", "manifest version does not match expected version")
    source_root = manifest.get("root")
    namespace = manifest.get("namespace", "current-v1")
    if not isinstance(source_root, str) or not source_root.strip():
        raise ImportErrorWithCode("source_root_invalid", "manifest root is required")
    if expected_source_root and source_root != expected_source_root:
        raise ImportErrorWithCode("foreign_source_root", "manifest sourceRoot differs from expected root")
    if expected_namespace and namespace != expected_namespace:
        raise ImportErrorWithCode("foreign_namespace", "manifest namespace differs from expected namespace")
    if manifest.get("objectLayout") != "objects/sha256/<first2>/<next2>/<sha256>.utf8":
        raise ImportErrorWithCode("object_layout_unsupported", "objectLayout is unsupported")
    receipt_path = root / "receipt.json"
    if receipt_path.exists():
        receipt = _read_json_file(root, "receipt.json")
        if receipt.get("manifestSha256") != manifest_sha:
            raise ImportErrorWithCode("receipt_manifest_hash_mismatch", "receipt manifestSha256 does not match manifest")
        if receipt.get("stats") != manifest.get("stats"):
            raise ImportErrorWithCode("receipt_stats_mismatch", "receipt stats differ from manifest stats")
    official = manifest.get("officialInspect")
    if isinstance(official, dict) and official.get("path") and official.get("sha256"):
        _read_json_file(root, official["path"], official["sha256"])
    inventory_raw = manifest.get("inventory")
    if not isinstance(inventory_raw, list):
        raise ImportErrorWithCode("inventory_invalid", "manifest inventory must be an array")
    normalized = []
    objects: list[BundleObject] = []
    for index, raw in enumerate(inventory_raw):
        if not isinstance(raw, dict):
            raise ImportErrorWithCode("inventory_entry_invalid", f"inventory.{index} must be an object")
        rel = normalize_rel(raw.get("path"), f"inventory.{index}.path")
        disposition = raw.get("disposition")
        if not isinstance(disposition, str) or not disposition:
            raise ImportErrorWithCode("disposition_invalid", f"inventory.{index}.disposition is required")
        source_kind = raw.get("sourceKind") if isinstance(raw.get("sourceKind"), str) else None
        ownership = raw.get("ownership") if isinstance(raw.get("ownership"), str) else None
        reason = raw.get("reason") if isinstance(raw.get("reason"), str) else None
        base = {"manifestIndex": index, "path": rel, "entryKind": raw.get("entryKind"), "sourceKind": source_kind,
                "ownership": ownership, "disposition": disposition, "reason": reason,
                "childFileCount": raw.get("childFileCount") if isinstance(raw.get("childFileCount"), int) else None}
        if disposition in CAPTURED_DISPOSITIONS:
            content_ref = normalize_rel(raw.get("contentRef"), f"inventory.{index}.contentRef")
            expected_sha = raw.get("sha256")
            expected_bytes = raw.get("size")
            expected_layout = f"objects/sha256/{expected_sha[:2]}/{expected_sha[2:4]}/{expected_sha}.utf8" if isinstance(expected_sha, str) else None
            if expected_layout and content_ref != expected_layout:
                raise ImportErrorWithCode("object_layout_mismatch", f"inventory.{index}.contentRef does not match sha256 layout")
            body = _validate_object(root, index, content_ref, expected_sha, expected_bytes)
            normalized.append({**base, "sha256": expected_sha, "bytes": expected_bytes, "objectPath": content_ref,
                               "mtime": raw.get("mtime"), "beforeAfterGuard": raw.get("beforeAfterGuard")})
            objects.append(BundleObject(index, content_ref, rel, source_kind or "current-v1", expected_sha, expected_bytes,
                                        "text/plain; charset=utf-8", source_kind,
                                        raw.get("mtime") if isinstance(raw.get("mtime"), str) else manifest.get("createdAt"),
                                        body, disposition=disposition, source_kind=source_kind, ownership=ownership, reason=reason))
        else:
            if any(key in raw for key in ("contentRef", "sha256", "size")):
                raise ImportErrorWithCode("excluded_content_metadata_forbidden", f"inventory.{index} non-captured entry carries content/hash metadata")
            normalized.append(base)
    stats = manifest.get("stats") if isinstance(manifest.get("stats"), dict) else {}
    if stats.get("inventoryEntries") is not None and stats.get("inventoryEntries") != len(normalized):
        raise ImportErrorWithCode("stats_inventory_mismatch", "stats.inventoryEntries mismatch")
    if stats.get("objectsWritten") is not None and stats.get("objectsWritten") != len({o.sha256 for o in objects}):
        raise ImportErrorWithCode("stats_objects_mismatch", "stats.objectsWritten mismatch")
    manifest["version"] = version
    manifest["sourceIdentity"] = _source_identity(manifest)
    manifest["_normalizedInventory"] = normalized
    return manifest, objects


def _load_delta_manifest(root: Path, manifest: dict[str, Any], manifest_sha: str,
                         expected_source_root: str | None, expected_namespace: str | None,
                         expected_version: str | None, expected_parent_manifest_sha256: str | None = None) -> tuple[dict[str, Any], list[BundleObject]]:
    version = manifest.get("deltaVersion")
    if not isinstance(version, str) or not version.strip():
        raise ImportErrorWithCode("manifest_version_invalid", "deltaVersion is required")
    if expected_version and version != expected_version:
        raise ImportErrorWithCode("version_mismatch", "delta version does not match expected version")
    parent = manifest.get("parent") if isinstance(manifest.get("parent"), dict) else {}
    parent_sha = parent.get("manifestSha256")
    if not isinstance(parent_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", parent_sha):
        raise ImportErrorWithCode("parent_manifest_invalid", "parent.manifestSha256 is required")
    if expected_parent_manifest_sha256 and parent_sha != expected_parent_manifest_sha256:
        raise ImportErrorWithCode("parent_manifest_mismatch", "delta parent manifest does not match expected parent")
    provenance = manifest.get("currentProvenance") if isinstance(manifest.get("currentProvenance"), dict) else {}
    source_root = provenance.get("root")
    namespace = manifest.get("namespace", "current-v1")
    if not isinstance(source_root, str) or not source_root.strip():
        raise ImportErrorWithCode("source_root_invalid", "currentProvenance.root is required")
    if expected_source_root and source_root != expected_source_root:
        raise ImportErrorWithCode("foreign_source_root", "delta source root differs from expected root")
    if expected_namespace and namespace != expected_namespace:
        raise ImportErrorWithCode("foreign_namespace", "delta namespace differs from expected namespace")
    if manifest.get("objectLayout") != "objects/sha256/<first2>/<next2>/<sha256>.utf8":
        raise ImportErrorWithCode("object_layout_unsupported", "objectLayout is unsupported")
    receipt_path = root / "receipt.json"
    if receipt_path.exists():
        receipt = _read_json_file(root, "receipt.json")
        if receipt.get("manifestSha256") != manifest_sha:
            raise ImportErrorWithCode("receipt_manifest_hash_mismatch", "receipt manifestSha256 does not match manifest")
        if receipt.get("parentManifestSha256") != parent_sha:
            raise ImportErrorWithCode("receipt_parent_hash_mismatch", "receipt parentManifestSha256 does not match manifest")
        if receipt.get("selectedCount") != parent.get("selectedCount"):
            raise ImportErrorWithCode("receipt_selected_count_mismatch", "receipt selectedCount differs from manifest parent")
        if receipt.get("stats") != manifest.get("stats"):
            raise ImportErrorWithCode("receipt_stats_mismatch", "receipt stats differ from manifest stats")
    inventory_raw = manifest.get("inventory")
    if not isinstance(inventory_raw, list):
        raise ImportErrorWithCode("inventory_invalid", "manifest inventory must be an array")
    normalized = []
    objects: list[BundleObject] = []
    for index, raw in enumerate(inventory_raw):
        if not isinstance(raw, dict):
            raise ImportErrorWithCode("inventory_entry_invalid", f"inventory.{index} must be an object")
        rel = normalize_rel(raw.get("path"), f"inventory.{index}.path")
        disposition = raw.get("disposition")
        if disposition not in ({DELTA_STRUCTURE_READY} | DELTA_TERMINAL_DISPOSITIONS):
            raise ImportErrorWithCode("disposition_invalid", f"inventory.{index}.disposition is unsupported")
        source_kind = raw.get("sourceKind") if isinstance(raw.get("sourceKind"), str) else None
        ownership = raw.get("ownership") if isinstance(raw.get("ownership"), str) else None
        reason = raw.get("reason") if isinstance(raw.get("reason"), str) else None
        base = {"manifestIndex": index, "path": rel, "entryKind": raw.get("entryKind"), "sourceKind": source_kind,
                "ownership": ownership, "knowledgeClass": raw.get("knowledgeClass") if isinstance(raw.get("knowledgeClass"), str) else None,
                "parentDisposition": raw.get("parentDisposition") if isinstance(raw.get("parentDisposition"), str) else None,
                "parentReason": raw.get("parentReason") if isinstance(raw.get("parentReason"), str) else None,
                "disposition": disposition, "reason": reason, "bytes": raw.get("size") if isinstance(raw.get("size"), int) else None,
                "mtime": raw.get("mtime") if isinstance(raw.get("mtime"), str) else None,
                "beforeAfterGuard": raw.get("beforeAfterGuard") if isinstance(raw.get("beforeAfterGuard"), str) else None}
        if raw.get("contentRef") is not None:
            content_ref = normalize_rel(raw.get("contentRef"), f"inventory.{index}.contentRef")
            expected_sha = raw.get("sha256")
            expected_bytes = raw.get("size")
            expected_layout = f"objects/sha256/{expected_sha[:2]}/{expected_sha[2:4]}/{expected_sha}.utf8" if isinstance(expected_sha, str) else None
            if expected_layout and content_ref != expected_layout:
                raise ImportErrorWithCode("object_layout_mismatch", f"inventory.{index}.contentRef does not match sha256 layout")
            body = _validate_object(root, index, content_ref, expected_sha, expected_bytes)
            normalized.append({**base, "sha256": expected_sha, "objectPath": content_ref})
            objects.append(BundleObject(index, content_ref, rel, source_kind or "current-v1-delta", expected_sha, expected_bytes,
                                        "text/plain; charset=utf-8", source_kind,
                                        raw.get("mtime") if isinstance(raw.get("mtime"), str) else manifest.get("createdAt"),
                                        body, disposition=disposition, source_kind=source_kind, ownership=ownership, reason=reason))
        else:
            if any(key in raw for key in ("contentRef", "sha256")):
                raise ImportErrorWithCode("excluded_content_metadata_forbidden", f"inventory.{index} excluded entry carries content/hash metadata")
            normalized.append(base)
    stats = manifest.get("stats") if isinstance(manifest.get("stats"), dict) else {}
    if stats.get("selectedEntries") is not None and stats.get("selectedEntries") != len(normalized):
        raise ImportErrorWithCode("stats_inventory_mismatch", "stats.selectedEntries mismatch")
    if stats.get("objectsWritten") is not None and stats.get("objectsWritten") != len({o.sha256 for o in objects}):
        raise ImportErrorWithCode("stats_objects_mismatch", "stats.objectsWritten mismatch")
    manifest["version"] = version
    manifest["sourceIdentity"] = {"namespace": namespace, "sourceRoot": source_root, "sourceGroup": "current-v1-heldunsupported-delta",
                                  "captureTime": manifest.get("createdAt"), "authority": manifest.get("authority"),
                                  "stats": stats, "parentManifestSha256": parent_sha,
                                  "parentCaptureVersion": parent.get("captureVersion"),
                                  "gitHeadContext": provenance.get("gitHeadContext")}
    manifest["_normalizedInventory"] = normalized
    return manifest, objects


def _load_legacy_manifest(root: Path, manifest: dict[str, Any], expected_source_root: str | None,
                          expected_namespace: str | None, expected_version: str | None) -> tuple[dict[str, Any], list[BundleObject]]:
    version = manifest.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ImportErrorWithCode("manifest_version_invalid", "manifest version is required")
    if expected_version and version != expected_version:
        raise ImportErrorWithCode("version_mismatch", "manifest version does not match expected version")
    identity = manifest.get("sourceIdentity")
    if not isinstance(identity, dict):
        raise ImportErrorWithCode("source_identity_invalid", "sourceIdentity object is required")
    source_root = identity.get("sourceRoot")
    namespace = identity.get("namespace")
    if not isinstance(source_root, str) or not source_root.strip():
        raise ImportErrorWithCode("source_root_invalid", "sourceIdentity.sourceRoot is required")
    if expected_source_root and source_root != expected_source_root:
        raise ImportErrorWithCode("foreign_source_root", "manifest sourceRoot differs from expected root")
    if expected_namespace and namespace != expected_namespace:
        raise ImportErrorWithCode("foreign_namespace", "manifest namespace differs from expected namespace")
    objects_raw = manifest.get("objects")
    if not isinstance(objects_raw, list):
        raise ImportErrorWithCode("objects_invalid", "manifest objects must be an array")
    objects: list[BundleObject] = []
    normalized = []
    for index, raw in enumerate(objects_raw):
        if not isinstance(raw, dict):
            raise ImportErrorWithCode("object_invalid", f"objects.{index} must be an object")
        object_path = normalize_rel(raw.get("objectPath"), f"objects.{index}.objectPath")
        original = normalize_rel(raw.get("originalRelativePath"), f"objects.{index}.originalRelativePath")
        source_group = raw.get("sourceGroup", identity.get("sourceGroup", "current-v1"))
        if not isinstance(source_group, str) or not source_group.strip():
            raise ImportErrorWithCode("source_group_invalid", f"objects.{index}.sourceGroup is required")
        expected = raw.get("sha256")
        expected_bytes = raw.get("bytes")
        body = _validate_object(root, index, object_path, expected, expected_bytes)
        objects.append(BundleObject(index, object_path, original, source_group, expected, expected_bytes,
                                    raw.get("mediaType") if isinstance(raw.get("mediaType"), str) else None,
                                    raw.get("sourceRole") if isinstance(raw.get("sourceRole"), str) else None,
                                    raw.get("captureTime") if isinstance(raw.get("captureTime"), str) else identity.get("captureTime"), body))
        normalized.append({"manifestIndex": index, "path": original, "entryKind": "file", "sourceKind": source_group,
                           "ownership": None, "disposition": "captured", "reason": "legacy-test-captured",
                           "sha256": expected, "bytes": expected_bytes, "objectPath": object_path})
    manifest["_normalizedInventory"] = normalized
    return manifest, objects


def load_and_validate_bundle(bundle: Path, *, expected_manifest_sha256: str | None = None,
                             expected_source_root: str | None = None,
                             expected_namespace: str | None = None,
                             expected_version: str | None = None,
                             expected_parent_manifest_sha256: str | None = None) -> tuple[dict[str, Any], str, list[BundleObject]]:
    try:
        root = bundle.resolve(strict=True)
    except OSError as exc:
        raise ImportErrorWithCode("bundle_unavailable", "bundle path is unavailable") from exc
    if not root.is_dir():
        raise ImportErrorWithCode("bundle_not_directory", "bundle path must be a directory")
    manifest_path = (root / "manifest.json").resolve(strict=True)
    if not inside(root, manifest_path) or manifest_path.is_symlink():
        raise ImportErrorWithCode("manifest_escape", "manifest escapes bundle root")
    if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ImportErrorWithCode("manifest_too_large", "manifest exceeds import bound")
    manifest_bytes = manifest_path.read_bytes()
    manifest_sha = sha256_bytes(manifest_bytes)
    if expected_manifest_sha256 and manifest_sha != expected_manifest_sha256:
        raise ImportErrorWithCode("manifest_hash_mismatch", "manifest sha256 does not match expected handoff hash")
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImportErrorWithCode("manifest_invalid", "manifest is not valid UTF-8 JSON") from exc
    if manifest.get("schemaVersion") == ACTUAL_EXPORT_SCHEMA_VERSION:
        manifest, objects = _load_actual_manifest(root, manifest, manifest_sha, expected_source_root, expected_namespace, expected_version)
    elif manifest.get("schemaVersion") == DELTA_EXPORT_SCHEMA_VERSION:
        manifest, objects = _load_delta_manifest(root, manifest, manifest_sha, expected_source_root, expected_namespace,
                                                 expected_version, expected_parent_manifest_sha256)
    elif manifest.get("schemaVersion") == EXPORT_SCHEMA_VERSION:
        manifest, objects = _load_legacy_manifest(root, manifest, expected_source_root, expected_namespace, expected_version)
    else:
        raise ImportErrorWithCode("manifest_schema_unsupported", "manifest schemaVersion is unsupported")
    return manifest, manifest_sha, objects


def line_offsets(text: str) -> list[int]:
    offsets = [0]
    for match in re.finditer("\n", text):
        offsets.append(match.end())
    return offsets


def fp_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def md_sections(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lines = text.splitlines()
    headings = []
    for idx, line in enumerate(lines, start=1):
        m = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if m:
            headings.append((idx, len(m.group(1)), m.group(2).strip()))
    if not headings:
        body = text.strip()
        if not body:
            return [], []
        return [{"kind": "document", "title": None, "lineStart": 1, "lineEnd": len(lines) or 1, "text": body}], []
    nodes = []
    links = []
    stack: list[tuple[int, int, str, str]] = []
    for h_index, (line, level, title) in enumerate(headings):
        end = (headings[h_index + 1][0] - 1) if h_index + 1 < len(headings) else len(lines)
        while stack and stack[-1][1] >= level:
            stack.pop()
        parent_id = stack[-1][3] if stack else None
        body = "\n".join(lines[line - 1:end]).strip()
        local_id = stable_id("section", line, level, title, fp_text(body))
        nodes.append({"id": local_id, "kind": "markdown-section", "title": title, "level": level,
                      "lineStart": line, "lineEnd": end, "text": body})
        if parent_id:
            links.append({"type": "parent-section", "from": local_id, "to": parent_id})
        stack.append((line, level, title, local_id))
    return nodes, links


def json_nodes(value: Any, prefix: str = "$", depth: int = 0) -> list[dict[str, Any]]:
    if depth > 3:
        return []
    nodes = []
    if isinstance(value, dict):
        summary = {k: value[k] for k in sorted(value)[:12]}
        nodes.append({"kind": "json-object", "jsonPath": prefix, "text": canonical_json(summary)[:4000]})
        for key in sorted(value)[:24]:
            nodes += json_nodes(value[key], f"{prefix}.{key}", depth + 1)
    elif isinstance(value, list):
        nodes.append({"kind": "json-array", "jsonPath": prefix, "text": f"array[{len(value)}]"})
        for i, item in enumerate(value[:24]):
            nodes += json_nodes(item, f"{prefix}[{i}]", depth + 1)
    return nodes


def parse_structural(obj: BundleObject, source_doc_fp: str) -> tuple[str, str, list[dict[str, Any]], list[dict[str, Any]], str | None]:
    suffix = Path(obj.original_relative_path).suffix.lower()
    if suffix not in SUPPORTED_TEXT_SUFFIXES:
        return "held", "unsupported-type-opaque", [], [], None
    try:
        text = obj.body.decode("utf-8")
    except UnicodeDecodeError:
        return "held", "invalid-utf8-opaque", [], [], None
    if "\x00" in text:
        return "held", "binary-looking-text-opaque", [], [], None
    if suffix in {".md", ".markdown", ".mdx", ".txt"}:
        nodes, links = md_sections(text)
    elif suffix in {".html", ".htm", ".tsv", ".csv", ".patch", ".diff"}:
        body = text.strip()
        if not body:
            return "held", "empty-or-no-structural-nodes", [], [], None
        nodes, links = [{"kind": "document", "title": None, "lineStart": 1, "lineEnd": len(text.splitlines()) or 1, "text": body[:40000]}], []
    elif suffix == ".xml":
        if re.search(r"<!\s*(DOCTYPE|ENTITY)\b", text, flags=re.I):
            return "held", "external-xml-entity-or-doctype-blocked", [], [], None
        try:
            root = ElementTree.fromstring(text)
        except ElementTree.ParseError:
            return "held", "invalid-xml-opaque", [], [], None
        nodes = []
        for index, elem in enumerate(root.iter()):
            snippet = " ".join((elem.text or "").split())[:1000]
            nodes.append({"kind": "xml-element", "xmlPath": elem.tag, "ordinal": index, "text": snippet})
        links = []
    elif suffix == ".jsonl":
        nodes = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                return "held", "invalid-jsonl-opaque", [], [], None
            for node in json_nodes(value, f"$[{line_no}]", 0)[:8]:
                node.update(kind=f"jsonl-{node['kind']}", lineStart=line_no, lineEnd=line_no)
                nodes.append(node)
        links = []
    elif suffix == ".json":
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return "held", "invalid-json-opaque", [], [], None
        nodes, links = json_nodes(value), []
    else:
        return "held", "unsupported-type-opaque", [], [], None
    if not nodes:
        return "held", "empty-or-no-structural-nodes", [], [], None
    enriched = []
    for ordinal, node in enumerate(nodes):
        body = node.get("text", "")
        node_id = stable_id("cand", obj.sha256, obj.original_relative_path, ordinal, node.get("lineStart"), node.get("jsonPath"), node.get("xmlPath"), fp_text(body))
        enriched.append({**node, "id": node_id, "ordinal": ordinal, "bodyFP": fp_text(body),
                         "sourceDocFP": source_doc_fp, "scopeVersion": obj.capture_time,
                         "reviewState": "pending-review", "reason": "captured-structural-candidate-not-verified"})
    return "structured", "captured-structural-pending-review", enriched, links, text


def read_previous_by_path(output_root: Path) -> dict[str, dict[str, str]]:
    previous: dict[str, dict[str, str]] = {}
    for ledger_path in sorted(output_root.glob("*/intake-ledger.jsonl")):
        if not ledger_path.is_file():
            continue
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            for p in row.get("sourcePaths", []):
                previous[p] = {"receiptId": row.get("receiptId"), "sourceDocFP": row.get("sourceDocFP")}
    return previous


def _require_import_trusted_anchors(expected_manifest_sha256: str | None, expected_source_root: str | None) -> None:
    """Import is a writing boundary; it must be bound to caller-trusted provenance."""
    if not expected_manifest_sha256 or not re.fullmatch(r"[0-9a-f]{64}", expected_manifest_sha256):
        raise ImportErrorWithCode("trusted_manifest_required", "import requires caller-trusted --expected-manifest-sha256")
    if not isinstance(expected_source_root, str) or not expected_source_root.strip():
        raise ImportErrorWithCode("trusted_source_root_required", "import requires caller-trusted --expected-source-root")


def import_bundle(bundle: Path, output_root: Path, *, expected_manifest_sha256: str | None = None,
                  expected_source_root: str | None = None, expected_namespace: str | None = None,
                  expected_version: str | None = None, dry_run: bool = False) -> dict[str, Any]:
    _require_import_trusted_anchors(expected_manifest_sha256, expected_source_root)
    manifest, manifest_sha, objects = load_and_validate_bundle(
        bundle, expected_manifest_sha256=expected_manifest_sha256,
        expected_source_root=expected_source_root, expected_namespace=expected_namespace,
        expected_version=expected_version)
    version = manifest["version"]
    normalized_inventory = manifest.get("_normalizedInventory", [])
    target_dir = output_root / version
    ledger_path = target_dir / "intake-ledger.jsonl"
    previous = read_previous_by_path(output_root)
    by_hash: dict[str, list[BundleObject]] = {}
    for obj in objects:
        by_hash.setdefault(obj.sha256, []).append(obj)
    candidates: list[dict[str, Any]] = []
    reference_links: list[dict[str, Any]] = []
    duplicate_groups: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    disposition_counts: dict[str, int] = {}
    source_kind_counts: dict[str, int] = {}
    for row in normalized_inventory:
        disp = row.get("disposition")
        if isinstance(disp, str):
            disposition_counts[disp] = disposition_counts.get(disp, 0) + 1
        sk = row.get("sourceKind")
        if isinstance(sk, str):
            source_kind_counts[sk] = source_kind_counts.get(sk, 0) + 1
    stats = manifest.get("stats") if isinstance(manifest.get("stats"), dict) else {}
    counts = {"manifestObjects": len(normalized_inventory) or len(objects),
              "inventoryEntries": len(normalized_inventory) or len(objects),
              "objectsWritten": len({o.sha256 for o in objects}),
              "captured": sum(disposition_counts.get(x, 0) for x in CAPTURED_DISPOSITIONS) or len(objects),
              "capturedNeedsReview": disposition_counts.get("captured_needs_review", 0),
              "excluded": sum(count for disp, count in disposition_counts.items() if disp.startswith("excluded")),
              "held": disposition_counts.get("heldunsupported", 0),
              "frameworkContext": disposition_counts.get("framework-context", 0),
              "structuredDocuments": 0, "structuredNodes": 0, "links": 0, "duplicateGroups": 0,
              "queuedUncertain": 0,
              "eligibleCaptured": sum(disposition_counts.get(x, 0) for x in CAPTURED_DISPOSITIONS) or len(objects),
              "processedEligible": 0,
              "sourceBytes": stats.get("capturedBytes", sum(o.bytes_count for o in objects)),
              "dispositionCounts": disposition_counts,
              "sourceKindCounts": source_kind_counts}
    objectless_rows = [row for row in normalized_inventory if row.get("disposition") not in CAPTURED_DISPOSITIONS]
    for row in objectless_rows:
        receipt = stable_id("receipt", version, row.get("path"), row.get("disposition"), row.get("reason"), row.get("manifestIndex"))
        item = {"receiptId": receipt, "version": version, "sourcePaths": [row.get("path")],
                "disposition": row.get("disposition"), "reason": row.get("reason"),
                "entryKind": row.get("entryKind"), "sourceKind": row.get("sourceKind"),
                "ownership": row.get("ownership"), "childFileCount": row.get("childFileCount"),
                "provenance": {"manifestSha256": manifest_sha, "sourceIdentity": manifest.get("sourceIdentity"),
                               "ownedUncertainDisposition": "metadata-only", "truthPromotion": "none"}}
        inventory.append({k: v for k, v in item.items() if v is not None})
        if row.get("disposition") == "heldunsupported":
            events.append({"eventId": stable_id("event", receipt, "pending-needs-type"), "receiptId": receipt,
                           "type": "typed-held", "reason": "pending-needs-type", "sourcePath": row.get("path")})
    for sha, group in sorted(by_hash.items()):
        paths = [o.original_relative_path for o in group]
        if len(paths) > 1:
            duplicate_groups.append({"duplicateGroupId": stable_id("dup", sha), "sha256": sha, "sourcePaths": paths})
        primary = group[0]
        if manifest.get("schemaVersion") != ACTUAL_EXPORT_SCHEMA_VERSION:
            legacy_reasons = sorted({r for p in paths if (r := private_reason(p))})
            if legacy_reasons:
                receipt = stable_id("receipt", version, sha, paths, "excluded")
                inventory.append({"receiptId": receipt, "sha256": sha, "sourcePaths": paths, "disposition": "excluded", "reason": legacy_reasons[0]})
                counts["excluded"] += len(group)
                counts["captured"] -= len(group)
                continue
        counts["eligibleCaptured"] = counts["eligibleCaptured"] or len(objects)
        source_doc_fp = sha
        disposition, reason, nodes, links, text = parse_structural(primary, source_doc_fp)
        receipt = stable_id("receipt", version, sha, paths, disposition, reason)
        supersedes = []
        for path in paths:
            prev = previous.get(path)
            if prev and prev.get("sourceDocFP") != source_doc_fp:
                supersedes.append(prev["receiptId"])
        group_source_kinds = sorted({o.source_kind or o.source_group for o in group if o.source_kind or o.source_group})
        group_ownership = sorted({o.ownership for o in group if o.ownership})
        base_doc = {"receiptId": receipt, "version": version, "sourceDocFP": source_doc_fp,
                    "sourcePaths": paths, "objectPaths": [o.object_path for o in group],
                    "bytes": primary.bytes_count, "sourceGroup": primary.source_group,
                    "sourceKinds": group_source_kinds, "ownership": group_ownership,
                    "sourceDisposition": sorted({o.disposition for o in group}),
                    "sourceRoleObserved": primary.source_role, "captureTime": primary.capture_time,
                    "provenance": {"manifestSha256": manifest_sha, "sourceIdentity": manifest.get("sourceIdentity"),
                                   "ownedUncertainDisposition": "pending-review", "truthPromotion": "none"},
                    "supersedesReceipt": sorted(set(x for x in supersedes if x))}
        inventory.append({**base_doc, "disposition": "captured" if disposition == "structured" else "held", "reason": reason})
        counts["processedEligible"] += len(group)
        if disposition == "structured":
            counts["structuredDocuments"] += 1
            for n in nodes:
                candidate = {**n, "candidateId": n["id"], "receiptId": receipt, "originalSource": paths,
                             "sourceKinds": group_source_kinds, "ownership": group_ownership,
                             "provenanceReceipt": receipt, "promotion": "deferred-not-verified"}
                candidates.append(candidate)
            for link in links:
                reference_links.append({**link, "receiptId": receipt, "reviewState": "pending-review"})
            counts["structuredNodes"] += len(nodes)
            counts["links"] += len(links)
            counts["queuedUncertain"] += len(nodes)
        else:
            events.append({"eventId": stable_id("event", receipt, reason), "receiptId": receipt, "type": "typed-held", "reason": reason})
    counts["duplicateGroups"] = len(duplicate_groups)
    receipt_fp = sha256_bytes("\n".join(canonical_json(row) for row in inventory).encode("utf-8"))
    result = {"ok": True, "schemaVersion": SCHEMA_VERSION, "mode": "current-v1-candidate-ingestion",
              "version": version, "generatedAt": utc_now(), "sourceTruthAutomatic": 0,
              "manifest": {"sha256": manifest_sha, "version": version, "sourceIdentity": manifest.get("sourceIdentity"),
                           "schemaVersion": manifest.get("schemaVersion"), "officialInspect": manifest.get("officialInspect")},
              "counts": counts, "receiptFP": receipt_fp,
              "publicImports": {"groups": sorted({row.get("sourceGroup") for row in inventory if row.get("sourceGroup")}),
                                "capturedReceipts": len([row for row in inventory if row.get("disposition") == "captured"]),
                                "excludedReceipts": len([row for row in inventory if str(row.get("disposition", "")).startswith("excluded")]),
                                "typedHeldReceipts": len([row for row in inventory if row.get("disposition") in ("held", "heldunsupported")]),
                                "queuedUncertain": counts["queuedUncertain"],
                                "structuredNodes": counts["structuredNodes"], "links": counts["links"],
                                "duplicateGroups": len(duplicate_groups), "events": len(events),
                                "errorIds": [], "sourceBytes": counts["sourceBytes"], "receiptFP": receipt_fp},
              "inventory": inventory, "duplicateGroups": duplicate_groups,
              "artifacts": {"result": str(target_dir / "result.json"), "ledger": str(ledger_path),
                            "candidates": str(target_dir / "candidates.jsonl"), "references": str(target_dir / "references.jsonl"),
                            "events": str(target_dir / "events.jsonl")},
              "deferrals": sorted({e["reason"] for e in events}), "errors": [],
              "notes": ["captured != verified fact", "structured != semantic confirmed", "no V2 DB or canonical record promotion"]}
    if dry_run:
        return result
    target_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(target_dir.parent)) as tmp:
        tmpdir = Path(tmp)
        (tmpdir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        for name, rows in (("intake-ledger.jsonl", inventory), ("candidates.jsonl", candidates),
                           ("references.jsonl", reference_links), ("events.jsonl", events)):
            with (tmpdir / name).open("w", encoding="utf-8") as f:
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        for name in ("result.json", "intake-ledger.jsonl", "candidates.jsonl", "references.jsonl", "events.jsonl"):
            os.replace(tmpdir / name, target_dir / name)
    return result


def import_delta_bundle(bundle: Path, output_root: Path, *, expected_manifest_sha256: str | None = None,
                        expected_source_root: str | None = None, expected_parent_manifest_sha256: str | None = None,
                        expected_namespace: str | None = None, expected_version: str | None = None,
                        dry_run: bool = False) -> dict[str, Any]:
    _require_import_trusted_anchors(expected_manifest_sha256, expected_source_root)
    if not expected_parent_manifest_sha256 or not re.fullmatch(r"[0-9a-f]{64}", expected_parent_manifest_sha256):
        raise ImportErrorWithCode("trusted_parent_manifest_required", "delta import requires caller-trusted --expected-parent-manifest-sha256")
    manifest, manifest_sha, objects = load_and_validate_bundle(
        bundle, expected_manifest_sha256=expected_manifest_sha256, expected_source_root=expected_source_root,
        expected_namespace=expected_namespace, expected_version=expected_version,
        expected_parent_manifest_sha256=expected_parent_manifest_sha256)
    if manifest.get("schemaVersion") != DELTA_EXPORT_SCHEMA_VERSION:
        raise ImportErrorWithCode("manifest_schema_unsupported", "import-delta requires a heldunsupported delta manifest")
    version = manifest["version"]
    parent_version = (manifest.get("parent") or {}).get("captureVersion")
    if parent_version:
        parent_result = output_root / parent_version / "result.json"
        if not parent_result.is_file():
            raise ImportErrorWithCode("parent_firstpass_missing", "delta import requires existing parent first-pass result")
        try:
            parent_data = json.loads(parent_result.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ImportErrorWithCode("parent_firstpass_invalid", "parent first-pass result is invalid") from exc
        if (parent_data.get("manifest") or {}).get("sha256") != expected_parent_manifest_sha256:
            raise ImportErrorWithCode("parent_firstpass_mismatch", "parent first-pass result manifest hash mismatch")
    target_dir = output_root / version
    normalized = manifest.get("_normalizedInventory", [])
    objects_by_path = {o.original_relative_path: o for o in objects}
    inventory: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    references: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    disposition_counts: dict[str, int] = {}
    knowledge_class_counts: dict[str, int] = {}
    structured_docs = structured_nodes = links_count = 0
    for row in normalized:
        disp = row.get("disposition")
        disposition_counts[disp] = disposition_counts.get(disp, 0) + 1
        kc = row.get("knowledgeClass")
        if isinstance(kc, str):
            knowledge_class_counts[kc] = knowledge_class_counts.get(kc, 0) + 1
        obj = objects_by_path.get(row.get("path"))
        source_doc_fp = row.get("sha256") or stable_id("source-metadata", version, row.get("path"), disp, row.get("reason"))
        receipt = stable_id("receipt", version, row.get("path"), source_doc_fp, disp, row.get("reason"))
        base = {"receiptId": receipt, "version": version, "sourceDocFP": source_doc_fp,
                "sourcePaths": [row.get("path")], "objectPaths": [row.get("objectPath")] if row.get("objectPath") else [],
                "bytes": row.get("bytes"), "sourceGroup": "current-v1-heldunsupported-delta",
                "sourceKinds": [row.get("sourceKind")] if row.get("sourceKind") else [],
                "ownership": [row.get("ownership")] if row.get("ownership") else [],
                "knowledgeClass": row.get("knowledgeClass"), "sourceDisposition": [disp],
                "parentDisposition": row.get("parentDisposition"), "parentReason": row.get("parentReason"),
                "reason": row.get("reason"), "captureTime": row.get("mtime"),
                "provenance": {"manifestSha256": manifest_sha, "parentManifestSha256": expected_parent_manifest_sha256,
                               "sourceIdentity": manifest.get("sourceIdentity"), "deltaDisposition": disp,
                               "ownedUncertainDisposition": "pending-review" if disp == DELTA_STRUCTURE_READY else "terminal-deferred",
                               "truthPromotion": "none"}}
        if disp == DELTA_STRUCTURE_READY and obj is not None:
            disposition, reason, nodes, links, _text = parse_structural(obj, source_doc_fp)
            base["disposition"] = "captured" if disposition == "structured" else "held"
            base["reason"] = reason
            if disposition == "structured":
                structured_docs += 1; structured_nodes += len(nodes); links_count += len(links)
                for n in nodes:
                    candidates.append({**n, "candidateId": n["id"], "receiptId": receipt,
                                       "originalSource": [row.get("path")], "sourceKinds": base["sourceKinds"],
                                       "ownership": base["ownership"], "knowledgeClass": row.get("knowledgeClass"),
                                       "provenanceReceipt": receipt, "promotion": "deferred-not-verified",
                                       "deltaDisposition": disp})
                for link in links:
                    references.append({**link, "receiptId": receipt, "reviewState": "pending-review"})
            else:
                events.append({"eventId": stable_id("event", receipt, reason), "receiptId": receipt,
                               "type": "typed-held", "reason": reason, "sourcePath": row.get("path"),
                               "deltaDisposition": disp})
        else:
            base["disposition"] = "deferred"
            events.append({"eventId": stable_id("event", receipt, disp, row.get("reason")), "receiptId": receipt,
                           "type": "delta-terminal", "reason": row.get("reason"), "sourcePath": row.get("path"),
                           "deltaDisposition": disp, "knowledgeClass": row.get("knowledgeClass")})
        inventory.append({k: v for k, v in base.items() if v not in (None, [], {})})
    stats = manifest.get("stats") if isinstance(manifest.get("stats"), dict) else {}
    counts = {"manifestObjects": len(normalized), "inventoryEntries": len(normalized),
              "objectsWritten": len({o.sha256 for o in objects}), "deltaSelectedEntries": len(normalized),
              "deltaDispositionCounts": disposition_counts, "knowledgeClassCounts": knowledge_class_counts,
              "eligibleCaptured": disposition_counts.get(DELTA_STRUCTURE_READY, 0),
              "processedEligible": disposition_counts.get(DELTA_STRUCTURE_READY, 0),
              "linkageOnlyNotKnowledge": disposition_counts.get("linkage-only/notknowledge", 0),
              "requiresTool": disposition_counts.get("requires-tool", 0),
              "needsHumanPrivateExcluded": disposition_counts.get("needs-human/private-excluded", 0),
              "safetyExcluded": disposition_counts.get("safety-excluded", 0),
              "structuredDocuments": structured_docs, "structuredNodes": structured_nodes,
              "links": links_count, "queuedUncertain": len(candidates),
              "remainingUnprocessed": stats.get("remainingUnprocessed", 0),
              "sourceBytes": stats.get("capturedBytes", sum(o.bytes_count for o in objects))}
    receipt_fp = sha256_bytes("\n".join(canonical_json(row) for row in inventory).encode("utf-8"))
    result = {"ok": True, "schemaVersion": SCHEMA_VERSION, "mode": "current-v1-heldunsupported-delta-ingestion",
              "version": version, "generatedAt": utc_now(), "sourceTruthAutomatic": 0,
              "manifest": {"sha256": manifest_sha, "version": version, "sourceIdentity": manifest.get("sourceIdentity"),
                           "schemaVersion": manifest.get("schemaVersion"), "parent": manifest.get("parent"),
                           "currentProvenance": manifest.get("currentProvenance")},
              "counts": counts, "receiptFP": receipt_fp,
              "publicImports": {"capturedReceipts": len([r for r in inventory if r.get("disposition") == "captured"]),
                                "terminalDeferredReceipts": len([r for r in inventory if r.get("disposition") == "deferred"]),
                                "queuedUncertain": len(candidates), "structuredNodes": structured_nodes,
                                "links": links_count, "events": len(events), "sourceBytes": counts["sourceBytes"],
                                "receiptFP": receipt_fp},
              "inventory": inventory, "duplicateGroups": [],
              "artifacts": {"result": str(target_dir / "result.json"), "ledger": str(target_dir / "intake-ledger.jsonl"),
                            "candidates": str(target_dir / "candidates.jsonl"), "references": str(target_dir / "references.jsonl"),
                            "events": str(target_dir / "events.jsonl")},
              "deferrals": sorted({e.get("deltaDisposition") for e in events if e.get("deltaDisposition")}),
              "errors": [], "notes": ["delta classification complete != semantic verified", "linkage-only/notknowledge is not queued as semantic fact", "no parent first-pass mutation"]}
    if dry_run:
        return result
    target_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(target_dir.parent)) as tmp:
        tmpdir = Path(tmp)
        (tmpdir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        for name, rows in (("intake-ledger.jsonl", inventory), ("candidates.jsonl", candidates),
                           ("references.jsonl", references), ("events.jsonl", events)):
            with (tmpdir / name).open("w", encoding="utf-8") as f:
                for item in rows:
                    f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
        for name in ("result.json", "intake-ledger.jsonl", "candidates.jsonl", "references.jsonl", "events.jsonl"):
            os.replace(tmpdir / name, target_dir / name)
    return result


def source_verified(bundle: str | Path, **kwargs: Any) -> dict[str, Any]:
    """Public mechanical proof: validate source bundle identity without writes."""
    manifest, manifest_sha, objects = load_and_validate_bundle(Path(bundle), **kwargs)
    normalized = manifest.get("_normalizedInventory", [])
    stats = manifest.get("stats") if isinstance(manifest.get("stats"), dict) else {}
    return {"ok": True, "schemaVersion": manifest.get("schemaVersion", EXPORT_SCHEMA_VERSION), "version": manifest["version"],
            "manifestSha256": manifest_sha, "objects": len(objects), "inventoryEntries": len(normalized) or len(objects),
            "objectsWritten": len({o.sha256 for o in objects}), "stats": stats,
            "sourceIdentity": manifest.get("sourceIdentity"), "sourceBytes": stats.get("capturedBytes", sum(o.bytes_count for o in objects))}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import a frozen CURRENT V1 export as pending local candidates.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("verify", "import", "import-delta"):
        p = sub.add_parser(name)
        p.add_argument("--bundle", required=True)
        p.add_argument("--expected-manifest-sha256")
        p.add_argument("--expected-source-root")
        p.add_argument("--expected-namespace")
        p.add_argument("--expected-version")
        if name in ("verify", "import-delta"):
            p.add_argument("--expected-parent-manifest-sha256")
        if name in ("import", "import-delta"):
            p.add_argument("--output-root", default=".local/current-v1-ingestion")
            p.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        common = {"expected_manifest_sha256": args.expected_manifest_sha256,
                  "expected_source_root": args.expected_source_root,
                  "expected_namespace": args.expected_namespace,
                  "expected_version": args.expected_version}
        if getattr(args, "expected_parent_manifest_sha256", None):
            common["expected_parent_manifest_sha256"] = args.expected_parent_manifest_sha256
        if args.cmd == "verify":
            out = source_verified(args.bundle, **common)
        elif args.cmd == "import-delta":
            out = import_delta_bundle(Path(args.bundle), Path(args.output_root), dry_run=args.dry_run, **common)
        else:
            out = import_bundle(Path(args.bundle), Path(args.output_root), dry_run=args.dry_run, **common)
        print(json.dumps(out, ensure_ascii=False, sort_keys=True))
        return 0
    except ImportErrorWithCode as exc:
        print(json.dumps({"ok": False, "errorId": stable_id("err", exc.code, exc.detail), "code": exc.code,
                          "detail": exc.detail}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
