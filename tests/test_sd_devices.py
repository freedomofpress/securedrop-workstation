import os

import pytest

from tests.base import (
    QubeWrapper,
)
from tests.base import (
    Test_SD_VM_Common as Test_SD_Devices_Common,  # noqa: F401 [HACK: import so base tests run]
)


@pytest.fixture(scope="module")
def qube():
    return QubeWrapper("sd-devices", expected_config_keys={"SD_MIME_HANDLING"})


def test_files_are_properly_copied(qube):
    assert qube.fileExists("/usr/bin/send-to-usb")
    assert qube.fileExists("/usr/share/applications/send-to-usb.desktop")
    assert qube.fileExists("/usr/share/mime/packages/application-x-sd-export.xml")


def test_sd_export_package_installed(qube):
    assert qube.package_is_installed("udisks2")
    assert qube.package_is_installed("securedrop-export")
    assert qube.package_is_installed("gnome-disk-utility")


def test_logging_configured(qube):
    qube.logging_configured()


def test_mime_types(qube):
    filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "vars", "sd-devices.mimeapps"
    )
    with open(filepath) as f:
        lines = f.readlines()
        for line in lines:
            if line != "[Default Applications]\n" and not line.startswith("#"):
                mime_type = line.split("=")[0]
                expected_app = line.split("=")[1].split(";")[0]
                actual_app = qube.run(f"xdg-mime query default {mime_type}")
                assert actual_app == expected_app


def test_mailcap_hardened(qube):
    qube.mailcap_hardened()


def test_open_in_dvm_desktop(qube):
    contents = qube.get_file_contents("/usr/share/applications/open-in-dvm.desktop")
    expected_contents = [
        "TryExec=/usr/bin/qvm-open-in-vm",
        "Exec=/usr/bin/qvm-open-in-vm --view-only @dispvm:sd-viewer %f",
    ]
    for line in expected_contents:
        assert line in contents
