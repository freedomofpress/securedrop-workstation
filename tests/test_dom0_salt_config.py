import subprocess

import pytest


def test_is_topfile_enabled():
    cmd = ["sudo", "qubesctl", "top.enabled"]
    wanted = "securedrop_salt.sd-workstation.top"

    try:
        all_topfiles = subprocess.check_output(cmd).decode("utf-8")
        assert wanted in all_topfiles

    except subprocess.CalledProcessError:
        pytest.fail("Error checking topfiles")
