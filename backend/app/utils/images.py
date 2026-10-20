"""Local image storage. Files stay on disk; MySQL stores the public URL."""

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings

JPEG = "image/jpeg"
PNG = "image/png"
WEBP = "image/webp"


class UploadRejected(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail


def detect_image(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None


def save_image(upload: UploadFile, folder: str) -> str:
    settings = get_settings()
    content = upload.file.read()
    if not content:
        raise UploadRejected("Image file is empty")
    if len(content) > settings.max_upload_bytes:
        raise UploadRejected("Image exceeds the size limit")
    extension = detect_image(content)
    if extension is None:
        raise UploadRejected("Upload a JPEG, PNG, or WebP image")
    directory = Path(settings.upload_dir) / folder
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{extension}"
    (directory / filename).write_bytes(content)
    return f"/media/{folder}/{filename}"


def delete_stored_file(url: str | None) -> None:
    if not url or not url.startswith("/media/"):
        return
    relative = url.removeprefix("/media/")
    path = Path(get_settings().upload_dir) / relative
    path.unlink(missing_ok=True)
