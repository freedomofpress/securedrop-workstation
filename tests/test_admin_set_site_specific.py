import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

# As written by securedrop-admin, i.e. yaml.safe_dump(..., default_flow_style=False)
SITE_SPECIFIC = """\
app_hostname: app
config_path: /home/amnesia/.config/securedrop-admin
daily_reboot_time: 4
securedrop_app_gpg_fingerprint: 65A1B5FF195B56353CC63DFFCC40EF1228271441
securedrop_supported_locales:
- de_DE
- en_US
ssh_users: sd
"""


@pytest.fixture
def script_path(proj_root: Path) -> Path:
    return proj_root / "admin_salt/securedrop-set-site-specific.py"


@pytest.fixture
def set_site_specific(load_non_standard_module: Callable, script_path: Path) -> Any:
    return load_non_standard_module(script_path)


@pytest.fixture
def site_specific(tmp_path: Path) -> Path:
    path = tmp_path / "site-specific"
    path.write_text(SITE_SPECIFIC)
    path.chmod(0o600)
    return path


def run(script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script_path, *args], capture_output=True, text=True, check=False
    )


def test_replaces_value(set_site_specific: Any, site_specific: Path) -> None:
    set_site_specific.set_value(site_specific, "config_path", "/home/user/.config/securedrop-admin")

    assert site_specific.read_text() == SITE_SPECIFIC.replace("/home/amnesia/", "/home/user/")


def test_adds_missing_key(set_site_specific: Any, site_specific: Path) -> None:
    set_site_specific.set_value(site_specific, "journalist_alert_email", "alerts@example.com")

    config = yaml.safe_load(site_specific.read_text())
    assert config["journalist_alert_email"] == "alerts@example.com"
    assert config["ssh_users"] == "sd"


def test_value_is_always_a_string(set_site_specific: Any, site_specific: Path) -> None:
    set_site_specific.set_value(site_specific, "securedrop_app_gpg_fingerprint", "1234")

    assert yaml.safe_load(site_specific.read_text())["securedrop_app_gpg_fingerprint"] == "1234"


def test_preserves_mode(set_site_specific: Any, site_specific: Path) -> None:
    set_site_specific.set_value(site_specific, "ssh_users", "admin")

    assert site_specific.stat().st_mode & 0o777 == 0o600
    # no leftover temporary file
    assert list(site_specific.parent.iterdir()) == [site_specific]


def test_rejects_non_mapping(set_site_specific: Any, tmp_path: Path) -> None:
    path = tmp_path / "site-specific"
    path.write_text("- not\n- a mapping\n")

    with pytest.raises(ValueError, match="does not contain a YAML mapping"):
        set_site_specific.set_value(path, "ssh_users", "sd")
    assert path.read_text() == "- not\n- a mapping\n"
    assert list(tmp_path.iterdir()) == [path]


def test_cli(script_path: Path, site_specific: Path) -> None:
    result = run(script_path, "--file", str(site_specific), "ssh_users", "admin")

    assert result.returncode == 0, result.stderr
    assert yaml.safe_load(site_specific.read_text())["ssh_users"] == "admin"


def test_cli_missing_file(script_path: Path, tmp_path: Path) -> None:
    result = run(script_path, "--file", str(tmp_path / "missing"), "ssh_users", "sd")

    assert result.returncode == 1
    assert "Error updating" in result.stderr
    assert not (tmp_path / "missing").exists()


def test_cli_invalid_key(script_path: Path, site_specific: Path) -> None:
    result = run(script_path, "--file", str(site_specific), "ssh users", "sd")

    assert result.returncode == 2
    assert "invalid key" in result.stderr
    assert site_specific.read_text() == SITE_SPECIFIC
