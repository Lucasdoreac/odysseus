import io

import pytest
from fastapi import HTTPException, UploadFile

import importlib
import src.config as config_mod
import src.upload_limits as upload_limits
import src.chat_helpers as chat_helpers
import src.upload_handler as upload_handler


@pytest.fixture(autouse=True)
def _restore_module():
    # Ensure later tests see the env-default module, not a test-mutated reload.
    yield
    importlib.reload(config_mod)
    importlib.reload(upload_limits)
    importlib.reload(chat_helpers)
    importlib.reload(upload_handler)


def _upload(name: str, data: bytes) -> UploadFile:
    return UploadFile(filename=name, file=io.BytesIO(data))


def test_chat_upload_limit_defaults_to_10mb(monkeypatch):
    monkeypatch.delenv("ODYSSEUS_CHAT_UPLOAD_MAX_BYTES", raising=False)
    importlib.reload(config_mod)
    mod = importlib.reload(upload_limits)

    assert mod.get_chat_upload_max_bytes() == 10 * 1024 * 1024


def test_chat_upload_limit_uses_env_bytes(monkeypatch):
    monkeypatch.setenv("ODYSSEUS_CHAT_UPLOAD_MAX_BYTES", "12345")
    importlib.reload(config_mod)
    mod = importlib.reload(upload_limits)

    assert mod.get_chat_upload_max_bytes() == 12345


def test_chat_upload_limit_rejects_invalid_env(monkeypatch):
    monkeypatch.setenv("ODYSSEUS_CHAT_UPLOAD_MAX_BYTES", "not-bytes")
    from pydantic import ValidationError
    with pytest.raises(ValidationError, match="ODYSSEUS_CHAT_UPLOAD_MAX_BYTES"):
        importlib.reload(config_mod)


def test_non_positive_chat_limit_rejected(monkeypatch):
    monkeypatch.setenv("ODYSSEUS_CHAT_UPLOAD_MAX_BYTES", "0")
    from pydantic import ValidationError
    with pytest.raises(ValidationError, match="greater than 0"):
        importlib.reload(config_mod)


def test_validate_file_upload_uses_configured_chat_limit(monkeypatch):
    monkeypatch.setenv("ODYSSEUS_CHAT_UPLOAD_MAX_BYTES", "4")
    importlib.reload(config_mod)
    importlib.reload(upload_limits)
    mod_helpers = importlib.reload(chat_helpers)

    with pytest.raises(HTTPException) as exc:
        mod_helpers.validate_file_upload(_upload("too-large.txt", b"abcde"))

    assert exc.value.status_code == 400
    assert exc.value.detail["error"] == "FILE_TOO_LARGE"
    assert exc.value.detail["message"] == "File size exceeds 4 bytes limit"


def test_upload_handler_uses_configured_chat_limit(monkeypatch, tmp_path):
    monkeypatch.setenv("ODYSSEUS_CHAT_UPLOAD_MAX_BYTES", "4")
    importlib.reload(config_mod)
    importlib.reload(upload_limits)
    mod_handler = importlib.reload(upload_handler)
    handler = mod_handler.UploadHandler(base_dir=str(tmp_path), upload_dir=str(tmp_path / "uploads"))

    with pytest.raises(HTTPException) as exc:
        handler.save_upload(_upload("too-large.txt", b"abcde"), client_ip="127.0.0.1")

    assert exc.value.status_code == 400
    assert exc.value.detail == "File size exceeds 4 bytes limit"
