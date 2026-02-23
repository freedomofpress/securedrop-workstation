#!/usr/bin/python3
"""
Tests for securedrop.GetSecretKeys qrexec service.
"""

import importlib.machinery
import importlib.util
import logging

import pytest

MODULE_PATH = "/etc/qubes-rpc/securedrop.GetSecretKeys"
MODULE_NAME = "securedrop_GetSecretKeys"


@pytest.fixture
def rpc_service():
    """Load the python RPC server module from its non-standard path"""

    # NOTE: loader needed since 'importlib.util.spec_from_file_location' only
    # works with '.py' files and RPC service does not have an extension
    loader = importlib.machinery.SourceFileLoader(MODULE_NAME, MODULE_PATH)

    spec = importlib.util.spec_from_loader(MODULE_NAME, loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def sd_gpg_env(monkeypatch):
    """
    Set calling qrexec domain as sd-gpg by default

    This is something that happens when a real service is being called
    """
    monkeypatch.setenv("QREXEC_REMOTE_DOMAIN", "sd-gpg")


def test_failure_unexpected_calling_qube(rpc_service, monkeypatch, caplog, capsys):
    """
    Simulate an RPC call from unexpected qube

    Similates an RPC policy misconfiguration that allows attacker to call from
    unexpected qube. Even in this case, the script should simply exit without any
    keys.
    """
    monkeypatch.setenv("QREXEC_REMOTE_DOMAIN", "evil-qube")

    with caplog.at_level(logging.ERROR), pytest.raises(SystemExit) as exc_info:
        rpc_service.main()
    assert exc_info.value.code == 1
    assert any("Security violation:" in r.message for r in caplog.records)

    # Nothing should be printed out (especially the key)
    assert capsys.readouterr().out == ""


def test_key_file_missing(rpc_service, tmp_path, caplog):
    rpc_service.SECRET_KEY_PATH = tmp_path / "does-not-exist.sec"

    with caplog.at_level(logging.ERROR), pytest.raises(SystemExit) as exc_info:
        rpc_service.main()
    assert exc_info.value.code == 2
    assert any("secret key file not found" in r.message for r in caplog.records)


def test_prints_key_contents(rpc_service, tmp_path, sd_gpg_env, capsys):
    # Key exists
    key_text = (
        "-----BEGIN PGP PRIVATE KEY BLOCK-----" "fakekey" "-----END PGP PRIVATE KEY BLOCK-----"
    )
    key_file = tmp_path / "sd-journalist.sec"
    key_file.write_text(key_text)
    rpc_service.SECRET_KEY_PATH = key_file

    # When the RPC service is called
    rpc_service.main()

    # Key is printed out
    assert key_text in capsys.readouterr().out
    assert capsys.readouterr().err == ""
