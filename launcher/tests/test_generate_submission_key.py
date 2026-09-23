import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parents[2] / "files/securedrop-generate-submission-key.py"


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A mock home directory, which the script's config paths are relative to"""
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


@pytest.fixture
def run_main(home, monkeypatch):
    # Load the module after HOME is set, so its config paths are in the mock homedir
    spec = importlib.util.spec_from_file_location("generate_submission_key", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    generate_submission_key = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generate_submission_key)

    def run(*args):
        monkeypatch.setattr(sys, "argv", ["securedrop-generate-submission-key", *args])
        generate_submission_key.main()

    return run


def test_generates_key(home, run_main):
    run_main("Placeholder Org")
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


def test_updates_existing_config(home, run_main):
    config_dir = home / ".config/securedrop-manage"
    config_dir.mkdir(parents=True)
    (config_dir / "config.json").write_text(json.dumps({"environment": "prod"}))
    run_main("Placeholder Org")
    config = json.loads((config_dir / "config.json").read_text())
    assert config.keys() == {"environment", "submission_key_fpr"}
    assert config["environment"] == "prod"


def test_refuses_overwrite(home, run_main):
    config_dir = home / ".config/securedrop-manage"
    config_dir.mkdir(parents=True)
    (config_dir / "sd-journalist.sec").write_text("existing")
    with pytest.raises(SystemExit):
        run_main("Placeholder Org")
    assert (config_dir / "sd-journalist.sec").read_text() == "existing"
    assert not (config_dir / "config.json").exists()
