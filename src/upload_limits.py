"""Small helpers for route-local upload size caps."""

from fastapi import HTTPException, UploadFile

from src.config import config


def format_byte_limit(limit: int) -> str:
    if limit % (1024 * 1024) == 0:
        return f"{limit // (1024 * 1024)} MB"
    if limit % 1024 == 0:
        return f"{limit // 1024} KB"
    return f"{limit} bytes"


def get_chat_upload_max_bytes() -> int:
    return config.uploads.chat


# Per-route upload byte-limits, single-sourced from config (issue #3364).
# Redefined as module-level constants to preserve backward compatibility with
# the existing imports in route files.
GALLERY_UPLOAD_MAX_BYTES = config.uploads.gallery
GALLERY_TRANSFORM_UPLOAD_MAX_BYTES = config.uploads.gallery_transform
MEMORY_IMPORT_MAX_BYTES = config.uploads.memory_import
PERSONAL_UPLOAD_MAX_BYTES = config.uploads.personal
EMAIL_COMPOSE_UPLOAD_MAX_BYTES = config.uploads.email_compose
STT_MAX_AUDIO_BYTES = config.uploads.stt
ICS_MAX_BYTES = config.uploads.ics


async def read_upload_limited(upload: UploadFile, limit: int, label: str = "Upload") -> bytes:
    """Read an UploadFile with a hard byte cap."""
    data = await upload.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(
            status_code=413,
            detail=f"{label} exceeds {format_byte_limit(limit)} limit",
        )
    return data
