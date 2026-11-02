"""
Integration tests for using a LUKS-encrypted USB device in the "sd-admin" VM.
"""

import shlex
import subprocess
from collections.abc import Iterator

import pytest

from securedrop_manage.products import PRODUCTS_PATH
from tests.base import QubeWrapper
from tests.markers import needs_admin
from tests.mock_usb import (
    close_usb_disks,
    create_usb_gadget,
    format_luks,
    remove_usb_gadget,
    udisks_call,
    wait_for_usb_disk,
)

pytestmark = needs_admin


@pytest.fixture(scope="module")
def no_journalist() -> None:
    """
    sys-usb auto-attaches USB storage to sd-devices when the Journalist
    Workstation is installed, which would race the manual attach to sd-admin
    """
    if (PRODUCTS_PATH / "journalist-workstation.json").is_file():
        pytest.skip("Journalist Workstation auto-attaches USB storage to sd-devices")


@pytest.fixture(scope="module")
def qube_sd_admin() -> QubeWrapper:
    return QubeWrapper("sd-admin")


@pytest.fixture(scope="module")
def qube_sys_usb() -> QubeWrapper:
    return QubeWrapper("sys-usb")


@pytest.fixture
def mock_usb_device(
    no_journalist: None, qube_sys_usb: QubeWrapper, qube_sd_admin: QubeWrapper
) -> Iterator[str]:
    """
    Creates a USB mass storage device in sys-usb, attaches it to sd-admin (as
    an admin would from the Qubes devices widget) and returns its disk name in
    sd-admin (e.g. "sda").
    """
    port = create_usb_gadget(qube_sys_usb)
    try:
        subprocess.run(["qvm-usb", "attach", qube_sd_admin.name, port], check=True)
        yield wait_for_usb_disk(qube_sd_admin)
    finally:
        close_usb_disks(qube_sd_admin)
        subprocess.run(["qvm-usb", "detach", qube_sd_admin.name, port], check=False)
        remove_usb_gadget(qube_sys_usb)


@pytest.fixture
def mock_usb_luks_device(qube_sd_admin: QubeWrapper, mock_usb_device: str) -> dict[str, str]:
    return format_luks(qube_sd_admin, mock_usb_device)


@pytest.mark.slow
@pytest.mark.configuration
@pytest.mark.run_alone  # Only one USB device can be attached at a time
def test_mount_luks_device(
    qube_sd_admin: QubeWrapper, mock_usb_luks_device: dict[str, str]
) -> None:
    partition = mock_usb_luks_device["partition"]
    passphrase = mock_usb_luks_device["passphrase"]
    content = "SecureDrop admin test"

    cleartext = udisks_call(qube_sd_admin, partition, "Encrypted.Unlock", f"'{passphrase}'", "{}")
    mountpoint = udisks_call(qube_sd_admin, cleartext, "Filesystem.Mount", "{}")
    test_file = shlex.quote(f"{mountpoint}/test.txt")
    qube_sd_admin.run(f"echo {shlex.quote(content)} > {test_file} && sync")
    written_content = qube_sd_admin.run(f"cat {test_file}")
    udisks_call(qube_sd_admin, cleartext, "Filesystem.Unmount", "{}")
    udisks_call(qube_sd_admin, partition, "Encrypted.Lock", "{}")
    assert written_content == content
