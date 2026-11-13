"""
Integration tests for exporting from the "sd-devices" VM to a LUKS-encrypted
USB device.
"""

import shlex
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.base import QubeWrapper
from tests.markers import needs_journalist
from tests.mock_usb import (
    close_usb_disks,
    create_usb_gadget,
    format_luks,
    remove_usb_gadget,
    unlocked_drive,
    wait_for_usb_disk,
)

pytestmark = needs_journalist


@pytest.fixture(scope="module")
def qube_sd_devices() -> QubeWrapper:
    return QubeWrapper("sd-devices")


@pytest.fixture(scope="module")
def qube_sys_usb() -> QubeWrapper:
    return QubeWrapper("sys-usb")


@pytest.fixture
def mock_usb_device(qube_sys_usb: QubeWrapper, qube_sd_devices: QubeWrapper) -> Iterator[str]:
    """
    Creates a USB mass storage device in sys-usb, which gets auto-attached to
    sd-devices, and returns its disk name in sd-devices (e.g. "sda").
    """
    create_usb_gadget(qube_sys_usb)
    try:
        # Wait for sys-usb's udev rule to attach the device to sd-devices
        yield wait_for_usb_disk(qube_sd_devices)
    finally:
        close_usb_disks(qube_sd_devices)
        remove_usb_gadget(qube_sys_usb)


@pytest.fixture
def mock_usb_luks_device(qube_sd_devices: QubeWrapper, mock_usb_device: str) -> dict[str, str]:
    return format_luks(qube_sd_devices, mock_usb_device)


EXPORT_SCRIPT = Path(__file__).parent / "files" / "export_to_device.py"


def _export(qube_sd_devices: QubeWrapper, passphrase: str, content: str) -> str:
    """Export a file to the USB device in sd-devices and return the status"""
    output = subprocess.run(
        [
            "qvm-run",
            "--pass-io",
            qube_sd_devices.name,
            "/opt/venvs/securedrop-export/bin/python3 -"
            f" {shlex.quote(passphrase)} {shlex.quote(content)}",
        ],
        input=EXPORT_SCRIPT.read_bytes(),
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.decode()
    return output.splitlines()[-1]


@pytest.mark.slow
@pytest.mark.configuration
@pytest.mark.run_alone  # Only one USB device can be attached for exporting
def test_export_to_luks_device(
    qube_sd_devices: QubeWrapper, mock_usb_luks_device: dict[str, str]
) -> None:
    partition = mock_usb_luks_device["partition"]
    passphrase = mock_usb_luks_device["passphrase"]
    content = "SecureDrop export test"

    assert _export(qube_sd_devices, passphrase, content) == "SUCCESS_EXPORT"

    # Export leaves the device locked: unlock it to check the exported file
    with unlocked_drive(qube_sd_devices, partition, passphrase) as mountpoint:
        exported_content = qube_sd_devices.run(
            f"cat {shlex.quote(mountpoint)}/sd-export-*/export_data/test.txt"
        )
        assert exported_content == content


@pytest.mark.slow
@pytest.mark.configuration
@pytest.mark.run_alone  # Only one USB device can be attached for exporting
def test_export_to_luks_device_bad_passphrase(
    qube_sd_devices: QubeWrapper, mock_usb_luks_device: dict[str, str]
) -> None:
    assert _export(qube_sd_devices, "wrong-passphrase", "test") == "ERROR_UNLOCK_LUKS"
