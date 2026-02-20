#!/usr/bin/python3
"""
Tests for securedrop.GetJournalistSecretKeys qrexec service.
"""

import importlib.util
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

MODULE_PATH = (
    Path(__file__).parent.parent.parent / "files" / "securedrop.GetJournalistSecretKeys.py"
)
MODULE_NAME = "securedrop_GetJournalistSecretKeys"


def _load_module():
    """Load the module from its non-standard path."""
    journal_stub = MagicMock()
    handler_stub = MagicMock(spec=logging.Handler)
    handler_stub.level = logging.NOTSET
    journal_stub.JournalHandler.return_value = handler_stub
    sys.modules.setdefault("systemd", journal_stub)
    sys.modules.setdefault("systemd.journal", journal_stub)

    spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


service = _load_module()

ORIGINAL_SECRET_KEY_PATH = service.SECRET_KEY_PATH

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def secret_key_file(tmp_path):
    """A real temp file standing in for the secret key, with the module patched to use it."""
    key_file = tmp_path / "sd-journalist.sec"
    key_file.write_text(
        "-----BEGIN PGP PRIVATE KEY BLOCK-----\nfakekey\n-----END PGP PRIVATE KEY BLOCK-----"
    )
    service.SECRET_KEY_PATH = key_file
    yield key_file
    service.SECRET_KEY_PATH = ORIGINAL_SECRET_KEY_PATH


@pytest.fixture
def missing_key_file(tmp_path):
    """Points the module at a path that does not exist."""
    service.SECRET_KEY_PATH = tmp_path / "does-not-exist.sec"
    yield
    service.SECRET_KEY_PATH = ORIGINAL_SECRET_KEY_PATH


@pytest.fixture
def sd_gpg_env(monkeypatch):
    monkeypatch.setenv("QREXEC_REMOTE_DOMAIN", "sd-gpg")


@pytest.mark.parametrize("qube_name", ["evil-qube", ""])
def test_rejects_unexpected_qube(monkeypatch, caplog, qube_name):
    monkeypatch.setenv("QREXEC_REMOTE_DOMAIN", qube_name)
    with caplog.at_level(logging.ERROR, logger=MODULE_NAME), pytest.raises(SystemExit) as exc_info:
        service.main()
    assert exc_info.value.code == 1
    assert any("Security violation" in r.message for r in caplog.records)


def test_rejects_missing_env_var(monkeypatch, caplog):
    monkeypatch.delenv("QREXEC_REMOTE_DOMAIN", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        service.main()
    with caplog.at_level(logging.ERROR, logger=MODULE_NAME), pytest.raises(SystemExit) as exc_info:
        service.main()
    assert exc_info.value.code == 1
    assert any("Security violation" in r.message for r in caplog.records)


def test_exits_when_key_file_missing(caplog, sd_gpg_env, missing_key_file):
    with caplog.at_level(logging.ERROR, logger=MODULE_NAME), pytest.raises(SystemExit) as exc_info:
        service.main()
    assert exc_info.value.code == 2
    assert any("secret key file not found" in r.message for r in caplog.records)


def test_prints_key_contents(sd_gpg_env, secret_key_file, capsys):
    service.main()
    assert secret_key_file.read_text().strip() in capsys.readouterr().out


def test_strips_trailing_whitespace(sd_gpg_env, secret_key_file, capsys):
    secret_key_file.write_text("\n\nsome key data\n\n")
    service.main()
    assert capsys.readouterr().out.strip() == "some key data"
