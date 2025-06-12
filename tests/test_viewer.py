import os
import subprocess

import pytest
from qubesadmin import Qubes

from tests.base import (
    QubeWrapper,
    Test_SD_VM_Local,  # noqa: F401 [HACK: import so base tests run]
)


def _create_test_qube(dispvm_template_name):
    # VM was running and needs a restart to test on the latest version
    if dispvm_template_name in Qubes().domains:
        _kill_test_qube(dispvm_template_name)

    # Create disposable based on specified template
    qube_name = f"{dispvm_template_name}-disposable"
    cmd_create_disp = (
        f"qvm-create --disp --property auto_cleanup=True "
        f"--template {dispvm_template_name} {qube_name}"
    )
    subprocess.run(cmd_create_disp.split(), check=True)

    return qube_name


def _kill_test_qube(qube_name):
    subprocess.run(["qvm-kill", qube_name], check=True)


@pytest.fixture(scope="module")
def qube():
    """
    Handles the creation of disposable qubes based on the provided DVM template
    """
    temp_qube_name = _create_test_qube("sd-viewer")

    yield QubeWrapper(
        temp_qube_name,
        expected_config_keys={"SD_MIME_HANDLING"},
        # this is not a comprehensive list, just a few that users are likely to use
        enforced_apparmor_profiles={
            "/usr/bin/evince",
            "/usr/bin/evince-previewer",
            "/usr/bin/evince-previewer//sanitized_helper",
            "/usr/bin/evince-thumbnailer",
            "/usr/bin/totem",
            "/usr/bin/totem-audio-preview",
            "/usr/bin/totem-video-thumbnailer",
            "/usr/bin/totem//sanitized_helper",
        },
    )

    # Tear Down
    _kill_test_qube(temp_qube_name)


def test_sd_viewer_metapackage_installed(qube):
    assert qube.package_is_installed("securedrop-workstation-viewer")
    assert not qube.package_is_installed("securedrop-workstation-svs-disp")


def test_sd_viewer_evince_installed(qube):
    pkg = "evince"
    assert qube.package_is_installed(pkg)


def test_sd_viewer_libreoffice_installed(qube):
    assert qube.package_is_installed("libreoffice")


def test_logging_configured(qube):
    qube.logging_configured()


def test_redis_packages_not_installed(qube):
    """
    Only the log collector, i.e. sd-log, needs redis, so redis will be
    present in small template, but not in large.
    """
    assert not qube.package_is_installed("redis")
    assert not qube.package_is_installed("redis-server")


def test_mime_types(qube):
    filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "vars", "sd-viewer.mimeapps"
    )
    with open(filepath) as f:
        lines = f.readlines()
        for line in lines:
            if line != "[Default Applications]\n" and not line.startswith("#"):
                mime_type = line.split("=")[0]
                expected_app = line.split("=")[1].rstrip()
                actual_app = qube.run(f"xdg-mime query default {mime_type}")
                assert actual_app == expected_app


def test_mimetypes_service(qube):
    qube.service_is_active("securedrop-mime-handling")


def test_mailcap_hardened(qube):
    qube.mailcap_hardened()


def test_mimetypes_symlink(qube):
    assert qube.fileExists(".local/share/applications/mimeapps.list")
    symlink_location = qube.get_symlink_location(".local/share/applications/mimeapps.list")
    assert symlink_location == "/opt/sdw/mimeapps.list.sd-viewer"
