import hashlib
import os
import subprocess
from pathlib import Path

import pytest

from tests.markers import needs_journalist

DESKTOP_FILE_NAME = "press.freedom.SecureDropUpdater.desktop"


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    ("wanted", "needs"),
    [
        ("securedrop_salt.sd-workstation.top", "needs_journalist"),
        ("admin_salt.sd-admin", "needs_admin"),
    ],
)
def test_is_topfile_enabled(wanted: str, needs: str, request: pytest.FixtureRequest) -> None:
    request.getfixturevalue(needs)

    all_topfiles = subprocess.check_output(["sudo", "qubesctl", "top.enabled"]).decode("utf-8")
    assert wanted in all_topfiles


@needs_journalist
@pytest.mark.provisioning
def test_trust_desktop_launcher() -> None:
    desktop_file = Path.home() / "Desktop" / DESKTOP_FILE_NAME

    # Duplicate the dbus session bootstrap logic from `../files/update-xfce-settings`,
    # so the test works under invocations that don't inherit a session bus,
    # such as OpenQA's `su user -c`.
    env = {**os.environ, "DBUS_SESSION_BUS_ADDRESS": f"unix:path=/run/user/{os.getuid()}/bus"}

    # salt should have already provisioned the correct checksum
    res = subprocess.run(
        ["gio", "info", "--attributes", "metadata::xfce-exe-checksum", desktop_file],
        text=True,
        check=False,
        capture_output=True,
        env=env,
    )
    assert res.returncode == 0, "desktop launcher does not match"
    assert checksum(desktop_file) in res.stdout
