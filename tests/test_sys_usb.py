import pytest

from tests.base import (
    QubeWrapper,
    Test_SD_VM_Local,  # noqa: F401 [HACK: import so base tests run]
)


@pytest.fixture(scope="module")
def qube():
    return QubeWrapper("sys-usb", linux_security_modules="selinux")


def test_files_are_properly_copied(qube):
    assert qube.fileExists("/etc/udev/rules.d/99-sd-devices.rules")
    assert qube.fileExists("/usr/local/bin/sd-attach-export-device")
