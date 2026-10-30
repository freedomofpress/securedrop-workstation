import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture

from securedrop_manage.products import Product

SCRIPT_PATH = Path(__file__).parent.parent / "files/securedrop-submission-key.py"


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A mock home directory, which the script's config paths are relative to"""
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


@pytest.fixture
def run_main(
    load_non_standard_module: Callable, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> Callable:
    """Load the python RPC server module from its non-standard path"""
    generate_submission_key = load_non_standard_module(SCRIPT_PATH)
    mocker.patch.object(
        generate_submission_key, "get_installed_product", return_value=Product.JOURNALIST
    )

    def run(*args: Any) -> None:
        monkeypatch.setattr(sys, "argv", ["securedrop-submission-key", *args])
        generate_submission_key.main()

    return run


def test_generates_key(home: Path, run_main: Callable) -> None:
    run_main("generate", "Placeholder Org")
    config_dir = home / ".config/securedrop-manage"
    secret_key = (config_dir / "sd-journalist.sec").read_text()
    public_key = (config_dir / "sd-journalist.pub").read_text()
    config = json.loads((config_dir / "config.json").read_text())

    assert secret_key.startswith("-----BEGIN PGP PRIVATE KEY BLOCK-----")
    assert public_key.startswith("-----BEGIN PGP PUBLIC KEY BLOCK-----")
    assert (config_dir / "sd-journalist.sec").stat().st_mode & 0o777 == 0o600

    output = subprocess.check_output(
        ["gpg", "--batch", "--with-colons", "--show-keys"], input=public_key, text=True
    )
    records = [line.split(":") for line in output.splitlines()]
    assert config == {"submission_key_fpr": next(r[9] for r in records if r[0] == "fpr")}
    assert [r[9] for r in records if r[0] == "uid"] == [
        "SecureDrop ([Placeholder Org] SecureDrop Submission Key)"
    ]


def test_updates_existing_config(home: Path, run_main: Callable) -> None:
    config_dir = home / ".config/securedrop-manage"
    config_dir.mkdir(parents=True)
    (config_dir / "config.json").write_text(json.dumps({"environment": "prod"}))
    run_main("generate", "Placeholder Org")
    config = json.loads((config_dir / "config.json").read_text())
    assert config.keys() == {"environment", "submission_key_fpr"}
    assert config["environment"] == "prod"


def test_refuses_overwrite(home: Path, run_main: Callable) -> None:
    config_dir = home / ".config/securedrop-manage"
    config_dir.mkdir(parents=True)
    (config_dir / "sd-journalist.sec").write_text("existing")
    with pytest.raises(SystemExit):
        run_main("generate", "Placeholder Org")
    assert (config_dir / "sd-journalist.sec").read_text() == "existing"
    assert not (config_dir / "config.json").exists()
