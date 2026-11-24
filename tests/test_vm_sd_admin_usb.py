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
    assert_usb_qrexec_denied,
    close_usb_disks,
    create_usb_gadget,
    format_luks,
    remove_usb_gadget,
    unlocked_drive,
    usb_autoattach_paused,
    wait_for_usb_disk,
)

pytestmark = needs_admin


@pytest.fixture(scope="module")
def qube() -> QubeWrapper:
    return QubeWrapper("sd-admin-usb", devices_attachable=True)


@pytest.fixture(scope="module")
def qube_sys_usb() -> QubeWrapper:
    return QubeWrapper("sys-usb")


def test_sd_admin_usb_package_installed(qube: QubeWrapper) -> None:
    assert qube.package_is_installed("udisks2")
    assert qube.package_is_installed("securedrop-admin-qubes")
    assert qube.package_is_installed("gnome-disk-utility")


def test_sd_admin_usb_config(qube: QubeWrapper, dom0_config_environment: str) -> None:
    """
    Confirm that qvm-prefs match expectations for sd-admin-usb VM.
    """
    vm = qube.vm
    nvm = vm.netvm
    assert nvm is None
    vm_type = vm.klass
    assert vm_type == "DispVM"
    assert SD_TAG in vm.tags
    # VM will be marked "internal" only in prod context.
    if dom0_config_environment == "prod":
        assert vm.features.get("internal") == "1"


def test_sd_admin_usb_dvm_config() -> None:
    """
    Confirm that qvm-prefs match expectations for the sd-admin-usb's DispVM template
    """
    dvm_qube = QubeWrapper("sd-admin-usb-dvm").vm
    nvm = dvm_qube.netvm
    assert nvm is None
    assert SD_TAG in dvm_qube.tags
    assert dvm_qube.template_for_dispvms


def test_usb_attach_arbitrary_device_denied(qube: QubeWrapper) -> None:
    assert_usb_qrexec_denied(qube)


@pytest.fixture
def mock_usb_device(qube_sys_usb: QubeWrapper, qube: QubeWrapper) -> Iterator[str]:
    """
    Creates a USB mass storage device in sys-usb, attaches it to sd-admin-usb
    (as an admin would from the Qubes devices widget) and returns its disk name
    in sd-admin-usb (e.g. "sda").

    If the Journalist Workstation is also installed, its auto-attach daemon is
    paused meanwhile, so it doesn't grab the device for sd-devices first.
    """
    with usb_autoattach_paused():
        port = create_usb_gadget(qube_sys_usb)
        try:
            subprocess.run(["qvm-usb", "attach", qube.name, port], check=True)
            yield wait_for_usb_disk(qube)
        finally:
            close_usb_disks(qube)
            subprocess.run(["qvm-usb", "detach", qube.name, port], check=False)
            remove_usb_gadget(qube_sys_usb)


@pytest.fixture
def mock_usb_luks_device(qube: QubeWrapper, mock_usb_device: str) -> dict[str, str]:
    return format_luks(qube, mock_usb_device)


@pytest.mark.slow
@pytest.mark.configuration
@pytest.mark.run_alone  # Only one USB device can be attached at a time
def test_mount_luks_device(qube: QubeWrapper, mock_usb_luks_device: dict[str, str]) -> None:
    partition = mock_usb_luks_device["partition"]
    passphrase = mock_usb_luks_device["passphrase"]
    content = "SecureDrop admin test"

    with unlocked_drive(qube, partition, passphrase) as mountpoint:
        test_file = shlex.quote(f"{mountpoint}/test.txt")
        qube.run(f"echo {shlex.quote(content)} > {test_file} && sync")
        written_content = qube.run(f"cat {test_file}")
        assert written_content == content
