"""
Integration tests for validating SecureDrop Workstation config,
specifically for the "sys-usb" VM and related functionality.
"""

import pytest

from tests.base import (
    QubeWrapper,
)
from tests.base import (
    Test_SD_VM_Common as Test_SD_SysUSB_Common,  # noqa: F401 [HACK: import so base tests run]
)
from tests.markers import needs_journalist

pytestmark = needs_journalist


@pytest.fixture(scope="module")
def qube() -> QubeWrapper:
    return QubeWrapper("sys-usb", linux_security_modules="selinux")


@pytest.mark.configuration
def test_usb_autoattach_files_removed(qube: QubeWrapper) -> None:
    assert not qube.fileExists("/etc/udev/rules.d/99-sd-devices.rules")
    assert not qube.fileExists("/rw/config/sd/etc/udev/rules.d/99-sd-devices.rules")
    assert not qube.fileExists("/usr/local/bin/sd-attach-export-device")
    assert "### BEGIN securedrop-workstation ###" not in qube.get_file_contents(
        "/rw/config/rc.local"
    )
