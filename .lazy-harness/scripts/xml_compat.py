#!/usr/bin/env python3
"""XML parse compatibility helpers for Python builds without working pyexpat."""
from __future__ import annotations

import pathlib
import re
import xml.etree.ElementTree as ET


_NAME_RE = re.compile(r"^[A-Za-z_][:A-Za-z0-9_.-]*")
_ENTITY_RE = re.compile(r"&(amp|lt|gt|apos|quot|#[0-9]+|#x[0-9A-Fa-f]+);")


class XMLParseError(ValueError):
    """Raised when the pure-Python fallback finds malformed XML."""


class SimpleElement:
    """Minimal ElementTree-compatible node used only when pyexpat is unavailable."""

    def __init__(self, tag: str, attrib: dict[str, str]) -> None:
        self.tag = tag
        self.attrib = attrib
        self._children: list[SimpleElement] = []
        self.text = ""

    def append(self, child: "SimpleElement") -> None:
        self._children.append(child)

    def findall(self, tag: str) -> list["SimpleElement"]:
        if tag.startswith(".//"):
            wanted = tag[3:]
            matches: list[SimpleElement] = []
            for child in self._children:
                if child.tag == wanted:
                    matches.append(child)
                matches.extend(child.findall(tag))
            return matches
        if tag.startswith("./"):
            parts = [part for part in tag[2:].split("/") if part]
            return self._find_path(parts)
        if "/" in tag:
            parts = [part for part in tag.split("/") if part]
            return self._find_path(parts)
        return [child for child in self._children if child.tag == tag]

    def _find_path(self, parts: list[str]) -> list["SimpleElement"]:
        if not parts:
            return [self]
        head, *tail = parts
        matches = [child for child in self._children if child.tag == head]
        if not tail:
            return matches
        found: list[SimpleElement] = []
        for match in matches:
            found.extend(match._find_path(tail))
        return found

    def findtext(self, tag: str) -> str | None:
        matches = self.findall(tag)
        if not matches:
            return None
        return matches[0].text

    def append_text(self, text: str) -> None:
        self.text += _decode_entities(text)


class SimpleElementTree:
    """Small subset of ElementTree used by lazy-harness self-tests."""

    def __init__(self, root: SimpleElement) -> None:
        self._root = root

    def getroot(self) -> SimpleElement:
        return self._root


def parse_xml_file(path: pathlib.Path) -> None:
    """Parse XML using ElementTree, with a pure-Python fallback when pyexpat is unavailable."""

    parse_xml_tree(path)


def parse_xml_tree(path: pathlib.Path):
    """Return an ElementTree-like object, falling back when pyexpat cannot load.

    Homebrew/macOS Python can import ``xml.etree.ElementTree`` while its pyexpat
    extension fails to load at parse time because the dynamic linker picks the
    system libexpat. The fallback preserves the harness doctor/self-test value:
    catch malformed XML without requiring platform-specific linker repair.
    """

    try:
        return ET.parse(path)
    except ImportError as exc:
        if not _is_expat_import_error(exc):
            raise
    except Exception:
        raise

    try:
        return parse_xml_text_pure(path.read_text(encoding="utf-8"))
    except XMLParseError as exc:
        raise XMLParseError(f"{exc}") from None


def parse_xml_text_pure(text: str) -> None:
    """Small well-formedness checker for harness XML fixtures.

    It validates XML shape and returns the root tree: processing instructions,
    comments, CDATA, doctypes, start/end/self-closing tags, quoted attributes,
    and built-in/numeric entities are supported. This keeps D01 deterministic
    on both Linux and macOS without a native expat dependency.
    """

    if text.startswith("\ufeff"):
        text = text[1:]

    stack: list[tuple[SimpleElement, int]] = []
    root: SimpleElement | None = None
    pos = 0
    root_count = 0
    length = len(text)

    while pos < length:
        lt = text.find("<", pos)
        if lt < 0:
            fragment = text[pos:]
            _validate_text_entities(fragment, pos)
            if stack:
                stack[-1][0].append_text(fragment)
            break

        fragment = text[pos:lt]
        _validate_text_entities(fragment, pos)
        if stack:
            stack[-1][0].append_text(fragment)

        if text.startswith("<!--", lt):
            end = text.find("-->", lt + 4)
            if end < 0:
                _raise(text, lt, "unterminated comment")
            pos = end + 3
            continue

        if text.startswith("<![CDATA[", lt):
            end = text.find("]]>", lt + 9)
            if end < 0:
                _raise(text, lt, "unterminated CDATA section")
            if stack:
                stack[-1][0].append_text(text[lt + 9 : end])
            pos = end + 3
            continue

        if text.startswith("<?", lt):
            end = text.find("?>", lt + 2)
            if end < 0:
                _raise(text, lt, "unterminated processing instruction")
            pos = end + 2
            continue

        if text.startswith("<!DOCTYPE", lt):
            end = _find_doctype_end(text, lt + 9)
            if end < 0:
                _raise(text, lt, "unterminated doctype")
            pos = end + 1
            continue

        gt = _find_tag_end(text, lt + 1)
        if gt < 0:
            _raise(text, lt, "unterminated tag")

        body = text[lt + 1 : gt].strip()
        if not body:
            _raise(text, lt, "empty tag")

        if body.startswith("/"):
            name = body[1:].strip()
            if not _NAME_RE.match(name) or any(ch.isspace() for ch in name):
                _raise(text, lt, "invalid closing tag")
            if not stack:
                _raise(text, lt, f"unexpected closing tag </{name}>")
            expected, _opened_at = stack.pop()
            if name != expected.tag:
                _raise(text, lt, f"mismatched closing tag </{name}>; expected </{expected.tag}>")
            pos = gt + 1
            continue

        self_closing = body.endswith("/")
        if self_closing:
            body = body[:-1].rstrip()

        name, after_name = _read_name(body, text, lt)
        attrs = _read_attributes(body[after_name:], text, lt + 1 + after_name)
        element = SimpleElement(name, attrs)
        if stack:
            stack[-1][0].append(element)
        else:
            root_count += 1
            if root_count > 1:
                _raise(text, lt, "multiple document elements")
            root = element
        if not self_closing:
            stack.append((element, lt))
        pos = gt + 1

    if stack:
        element, opened_at = stack[-1]
        _raise(text, opened_at, f"unclosed tag <{element.tag}>")
    if root is None:
        _raise(text, 0, "missing document element")
    return SimpleElementTree(root)


def _is_expat_import_error(exc: ImportError) -> bool:
    message = str(exc)
    return "expat" in message or "pyexpat" in message


def _find_tag_end(text: str, pos: int) -> int:
    quote: str | None = None
    while pos < len(text):
        ch = text[pos]
        if quote:
            if ch == quote:
                quote = None
        elif ch in {'"', "'"}:
            quote = ch
        elif ch == ">":
            return pos
        pos += 1
    return -1


def _find_doctype_end(text: str, pos: int) -> int:
    quote: str | None = None
    bracket_depth = 0
    while pos < len(text):
        ch = text[pos]
        if quote:
            if ch == quote:
                quote = None
        elif ch in {'"', "'"}:
            quote = ch
        elif ch == "[":
            bracket_depth += 1
        elif ch == "]" and bracket_depth:
            bracket_depth -= 1
        elif ch == ">" and bracket_depth == 0:
            return pos
        pos += 1
    return -1


def _read_name(body: str, full_text: str, tag_start: int) -> tuple[str, int]:
    match = _NAME_RE.match(body)
    if not match:
        _raise(full_text, tag_start, "invalid tag name")
    return match.group(0), match.end()


def _read_attributes(attr_text: str, full_text: str, base_pos: int) -> dict[str, str]:
    pos = 0
    attrs: dict[str, str] = {}
    while pos < len(attr_text):
        while pos < len(attr_text) and attr_text[pos].isspace():
            pos += 1
        if pos >= len(attr_text):
            return attrs

        match = _NAME_RE.match(attr_text[pos:])
        if not match:
            _raise(full_text, base_pos + pos, "invalid attribute name")
        name = match.group(0)
        if name in attrs:
            _raise(full_text, base_pos + pos, f"duplicate attribute {name!r}")
        pos += match.end()

        while pos < len(attr_text) and attr_text[pos].isspace():
            pos += 1
        if pos >= len(attr_text) or attr_text[pos] != "=":
            _raise(full_text, base_pos + pos, f"missing '=' after attribute {name!r}")
        pos += 1
        while pos < len(attr_text) and attr_text[pos].isspace():
            pos += 1
        if pos >= len(attr_text) or attr_text[pos] not in {'"', "'"}:
            _raise(full_text, base_pos + pos, f"missing quoted value for attribute {name!r}")
        quote = attr_text[pos]
        pos += 1
        value_start = pos
        while pos < len(attr_text) and attr_text[pos] != quote:
            pos += 1
        if pos >= len(attr_text):
            _raise(full_text, base_pos + value_start - 1, f"unterminated value for attribute {name!r}")
        value = attr_text[value_start:pos]
        if "<" in value:
            _raise(full_text, base_pos + value_start + value.index("<"), "'<' in attribute value")
        _validate_text_entities(value, base_pos + value_start)
        attrs[name] = value
        pos += 1
    return attrs

def _validate_text_entities(fragment: str, base_pos: int) -> None:
    amp = fragment.find("&")
    while amp >= 0:
        match = _ENTITY_RE.match(fragment, amp)
        if not match:
            _raise(fragment, amp, "invalid entity reference", base_pos=base_pos)
        amp = fragment.find("&", match.end())


def _decode_entities(fragment: str) -> str:
    return (
        fragment.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&apos;", "'")
        .replace("&quot;", '"')
        .replace("&amp;", "&")
    )


def _raise(text: str, pos: int, message: str, *, base_pos: int = 0) -> None:
    absolute = base_pos + pos
    line = text.count("\n", 0, pos) + 1
    line_start = text.rfind("\n", 0, pos) + 1
    column = pos - line_start + 1
    raise XMLParseError(f"line {line}, column {column}: {message} (offset {absolute})")
