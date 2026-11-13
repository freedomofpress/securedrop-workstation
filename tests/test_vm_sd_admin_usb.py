"""
Integration tests for using a LUKS-encrypted USB device in the "sd-admin-usb" VM.
"""

import shlex
import subprocess
from collections.abc import Iterator

import pytest

from tests.base import SD_TAG, QubeWrapper
from tests.base import (
    Test_SD_VM_Common as Test_SD_Admin_USB_Common,  # noqa: F401 [HACK: import so base tests run]
)
from tests.markers import needs_admin
from tests.mock_usb import (
    close_usb_disks,
    create_usb_gadget,
    format_luks,
    remove_usb_gadget,
    unlocked_drive,
    wait_for_usb_disk,
)

pytestmark = needs_admin


@pytest.fixture(scope="module")
def qube_sd_admin_usb() -> QubeWrapper:
    return QubeWrapper("sd-admin-usb")


@pytest.fixture(scope="module")
def qube_sys_usb() -> QubeWrapper:
    return QubeWrapper("sys-usb")


def test_sd_admin_usb_package_installed(qube_sd_admin_usb: QubeWrapper) -> None:
    assert qube_sd_admin_usb.package_is_installed("udisks2")
    assert qube_sd_admin_usb.package_is_installed("securedrop-admin-qubes")
    assert qube_sd_admin_usb.package_is_installed("gnome-disk-utility")


def test_sd_admin_usb_config(qube_sd_admin_usb: QubeWrapper) -> None:
    """
    Confirm that qvm-prefs match expectations for sd-admin-usb VM.
    """
    vm = qube_sd_admin_usb.vm
    nvm = vm.netvm
    assert nvm is None
    vm_type = vm.klass
    assert vm_type == "DispVM"
    assert SD_TAG in vm.tags


def test_sd_admin_usb_dvm_config() -> None:
    """
    Confirm that qvm-prefs match expectations for the sd-admin-usb's DispVM template
    """
    dvm_qube = QubeWrapper("sd-admin-usb-dvm").vm
    nvm = dvm_qube.netvm
    assert nvm is None
    assert SD_TAG in dvm_qube.tags
    assert dvm_qube.template_for_dispvms


@pytest.fixture
def mock_usb_device(
    qube_sys_usb: QubeWrapper, qube_sd_admin_usb: QubeWrapper, needs_journalist_absent: None
) -> Iterator[str]:
    """
    Creates a USB mass storage device in sys-usb, attaches it to sd-admin (as
    an admin would from the Qubes devices widget) and returns its disk name in
    sd-admin (e.g. "sda").
    """
    port = create_usb_gadget(qube_sys_usb)
    try:
        subprocess.run(["qvm-usb", "attach", qube_sd_admin_usb.name, port], check=True)
        yield wait_for_usb_disk(qube_sd_admin_usb)
    finally:
        close_usb_disks(qube_sd_admin_usb)
        subprocess.run(["qvm-usb", "detach", qube_sd_admin_usb.name, port], check=False)
        remove_usb_gadget(qube_sys_usb)


@pytest.fixture
def mock_usb_luks_device(qube_sd_admin_usb: QubeWrapper, mock_usb_device: str) -> dict[str, str]:
    return format_luks(qube_sd_admin_usb, mock_usb_device)


@pytest.mark.slow
@pytest.mark.configuration
@pytest.mark.run_alone  # Only one USB device can be attached at a time
def test_mount_luks_device(
    qube_sd_admin_usb: QubeWrapper, mock_usb_luks_device: dict[str, str]
) -> None:
    partition = mock_usb_luks_device["partition"]
    passphrase = mock_usb_luks_device["passphrase"]
    content = "SecureDrop admin test"

    with unlocked_drive(qube_sd_admin_usb, partition, passphrase) as mountpoint:
        test_file = shlex.quote(f"{mountpoint}/test.txt")
        qube_sd_admin_usb.run(f"echo {shlex.quote(content)} > {test_file} && sync")
        written_content = qube_sd_admin_usb.run(f"cat {test_file}")
        assert written_content == content
