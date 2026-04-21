import hashlib
import subprocess
from pathlib import Path

import pytest

from tests.conftest import skip_on_qubes_4_2

DESKTOP_FILE_NAME = "press.freedom.SecureDropUpdater.desktop"


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_is_topfile_enabled():
    cmd = ["sudo", "qubesctl", "top.enabled"]
    wanted = "securedrop_salt.sd-workstation.top"

    try:
        all_topfiles = subprocess.check_output(cmd).decode("utf-8")
        assert wanted in all_topfiles

    except subprocess.CalledProcessError:
        pytest.fail("Error checking topfiles")


@skip_on_qubes_4_2
@pytest.mark.provisioning
def test_trust_desktop_launcher():
    desktop_file = Path.home() / "Desktop" / DESKTOP_FILE_NAME

    # salt should have already provisioned the correct checksum
    res = subprocess.run(
        ["gio", "info", "--attributes", "metadata::xfce-exe-checksum", desktop_file],
        text=True,
        check=False,
        capture_output=True,
    )
    assert res.returncode == 0, "desktop launcher does not match"
    assert checksum(desktop_file) in res.stdout
