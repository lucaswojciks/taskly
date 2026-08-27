"""File-format helpers for attachments.

Type detection is by leading "magic bytes", never by the client-declared
Content-Type or the filename extension (see docs/specs/attachments.md §4.1).
"""

import re
import unicodedata

_MAGIC_PREFIXES: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"%PDF-", "application/pdf"),
)
_EXTENSION: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "application/pdf": "pdf",
}
_MAX_STEM = 200
_UNSAFE = re.compile(r"[/\\\x00-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s+")

# Bytes needed to identify every supported type (WebP checks offsets 0-3 and 8-11).
SNIFF_BYTES = 16


def detect_content_type(head: bytes) -> str | None:
    """Return the canonical content-type of an allowed file, or None."""
    for prefix, content_type in _MAGIC_PREFIXES:
        if head.startswith(prefix):
            return content_type
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return None


def extension_for(content_type: str) -> str:
    return _EXTENSION[content_type]


def sanitize_filename(raw: str | None, *, content_type: str) -> str:
    """Display-only file name. Never used to build the storage object key."""
    name = unicodedata.normalize("NFC", (raw or "").strip())
    name = _UNSAFE.sub("", name)
    name = _WHITESPACE.sub(" ", name).strip(" .")
    stem = name.rsplit(".", 1)[0] if "." in name else name
    stem = stem[:_MAX_STEM].strip() or "file"
    return f"{stem}.{extension_for(content_type)}"
