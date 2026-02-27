import subprocess
from pathlib import Path

import pytest

from tests.conftest import skip_on_qubes_4_2


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
    # salt should have already provisioned the correct checksum
    res = subprocess.run(["/usr/bin/securedrop/sdw-desktop-trust", "--check"], check=False)
    assert res.returncode == 0, "desktop launcher is correctly trusted"

    desktop_file = Path.home() / "Desktop" / "press.freedom.SecureDropUpdater.desktop"
    # Manually modify the checksum to a clearly invalid value
    subprocess.check_call(
        ["gio", "set", "-t", "string", str(desktop_file), "metadata::xfce-exe-checksum", "invalid"]
    )

    res = subprocess.run(["/usr/bin/securedrop/sdw-desktop-trust", "--check"], check=False)
    assert res.returncode == 1, "desktop launcher checksum shouldn't match"

    res = subprocess.run(
        ["/usr/bin/securedrop/sdw-desktop-trust"], text=True, check=False, capture_output=True
    )
    assert "sdw-desktop-trust: set xfce-exe-checksum on" in res.stdout

    res = subprocess.run(["/usr/bin/securedrop/sdw-desktop-trust", "--check"], check=False)
    assert res.returncode == 0, "desktop launcher is correctly trusted"
