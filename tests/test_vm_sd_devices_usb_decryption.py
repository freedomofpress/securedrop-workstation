"""
Integration tests for exporting from the "sd-devices" VM to a LUKS-encrypted
USB device.
"""

import os
import re
import shlex
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tests.base import QubeWrapper

IS_CI = os.environ.get("CI") == "true"

# Seconds to wait for a udisks2 call: LUKS formatting can take longer than
# gdbus' default 25s, especially on slower CI hardware
UDISKS_TIMEOUT = 300 if IS_CI else 30


@pytest.fixture(scope="module")
def qube() -> QubeWrapper:
    return QubeWrapper("sd-devices")


@pytest.fixture(scope="module")
def qube_sys_usb() -> QubeWrapper:
    return QubeWrapper("sys-usb")


def _udisks_call(qube: QubeWrapper, object_path: str, method: str, *args: str) -> str:
    """
    Call a udisks2 D-Bus method as the desktop user (as GNOME Disks does) and
    return its result (an object path or a mount point), if any
    """
    try:
        output = qube.run(
            f"gdbus call --system --timeout {UDISKS_TIMEOUT} --dest org.freedesktop.UDisks2 "
            f"--object-path {object_path} --method org.freedesktop.UDisks2.{method} "
            f"{shlex.join(args)}"
        )
    except subprocess.CalledProcessError:
        pytest.fail(f"Failed udisks2 call '{method}'")

    # gdbus prints e.g. "(objectpath '/org/.../sda1',)", "('/media/...',)" or "()"
    match = re.search(r"'(.*)'", output)
    return match.group(1) if match else ""


# Unmounts and closes anything left on USB disks in sd-devices (e.g. by a test
# that failed midway), so the device can be removed cleanly
CLOSE_USB_DISKS = (
    "for disk in $(lsblk -dnpo NAME,TRAN | awk '$2 == \"usb\" {print $1}'); do"
    " lsblk -nrpo NAME,MOUNTPOINT $disk | awk '$2 != \"\" {print $1}' | xargs -r umount;"
    " lsblk -nrpo NAME,TYPE $disk | awk '$2 == \"crypt\" {print $1}' | xargs -r dmsetup remove;"
    " done; udevadm settle"
)


class QubesExtraTestCaseVMAdapter:
    """
    Adapts standard qubesadmin VM interface to what's needed by
    qubesusbproxy.tests

    This is necessary SecureDrop tests can't be derived directly from
    qubes.tests.ExtraTestCase (it's written for a different test platform
    and assumes tests run in a temporary qubesd and not the actual test
    system with all VMs created already).

    In this specific case, Qubes' extra tests has a VMWrapper [^1] to
    "Wrap VM object to provide stable API for basic operations". We reduce
    the interface to just the bare minimum what Qubes' USB tests need and
    built on top of QubeWrapper (which uses qubesadmin under the hood) and
    not the VMWrapper.

    [^1]: https://github.com/QubesOS/qubes-core-admin/blob/3436d93/qubes/tests/extra.py#L64
    """

    def __init__(self, qube: QubeWrapper) -> None:
        self.vm = qube.vm

    def start(self) -> None:
        if not self.vm.is_running():
            self.vm.start()

    def is_running(self) -> bool:
        return self.vm.is_running()

    def run(self, command: str, **kwargs: Any) -> SimpleNamespace:
        out, err = self.vm.run(command, user="root")
        return SimpleNamespace(returncode=0, communicate=lambda: (out, err))


@pytest.fixture
def mock_usb_device(qube_sys_usb: QubeWrapper, qube: QubeWrapper) -> Iterator[str]:
    """
    Creates a USB mass storage device in sys-usb, which gets auto-attached to
    sd-devices, and returns its disk name in sd-devices (e.g. "sda").

    The device is created with the helpers from Qubes' own USB proxy tests
    (qubesusbproxy/tests.py, shipped in dom0 by qubes-usb-proxy-dom0).
    """
    usbproxy_tests = pytest.importorskip("qubesusbproxy.tests")
    sys_usb_adapter = QubesExtraTestCaseVMAdapter(qube_sys_usb)

    # Teardown only unbinds it, so a previous test leaves it behind
    if qube_sys_usb.fileExists("/sys/kernel/config/usb_gadget/test_g1"):
        usbproxy_tests.recreate_usb_gadget(sys_usb_adapter)
    else:
        usbproxy_tests.create_usb_gadget(sys_usb_adapter)

    try:
        # Wait for sys-usb's udev rule to attach the device to sd-devices
        disk = ""
        for _ in range(60):
            disk = qube.run("lsblk -dno NAME,TRAN | awk '$2 == \"usb\" {print $1}'")
            if disk:
                break
            time.sleep(1)
        assert disk, "USB device was not attached to sd-devices"

        yield disk
    finally:
        qube.run(CLOSE_USB_DISKS, user="root")
        # Like usbproxy_tests.remove_usb_gadget(), which the adapter doesn't support
        qube_sys_usb.run("echo > /sys/kernel/config/usb_gadget/test_g1/UDC", user="root")


@pytest.fixture
def mock_usb_luks_device(qube: QubeWrapper, mock_usb_device: str) -> dict[str, str]:
    """
    Formats the mock USB device with LUKS + ext4.

    The formatting follows the Transfer Device docs (GNOME Disks → Format
    Partition… → "Password protect volume (LUKS)" + Ext4), done through the
    same udisks2 calls GNOME Disks makes. The volume is left locked.
    https://docs.securedrop.org/en/stable/admin/installation/set_up_transfer_and_export_device.html
    """
    passphrase = "correct-horse-battery-staple"

    block_path = f"/org/freedesktop/UDisks2/block_devices/{mock_usb_device}"
    _udisks_call(qube, block_path, "Block.Format", "'gpt'", "{}")
    partition = _udisks_call(
        qube, block_path, "PartitionTable.CreatePartition", "0", "0", "''", "''", "{}"
    )
    _udisks_call(
        qube,
        partition,
        "Block.Format",
        "'ext4'",
        f"{{'label': <'Transfer Device'>, 'encrypt.passphrase': <'{passphrase}'>,"
        " 'take-ownership': <true>}",
    )
    # Formatting leaves it unlocked: lock it, like a freshly plugged-in device
    _udisks_call(qube, partition, "Encrypted.Lock", "{}")

    return {"partition": partition, "passphrase": passphrase}


EXPORT_SCRIPT = Path(__file__).parent / "files" / "export_to_device.py"


def _export(qube: QubeWrapper, passphrase: str, content: str) -> str:
    """Export a file to the USB device in sd-devices and return the status"""
    output = subprocess.run(
        [
            "qvm-run",
            "--pass-io",
            qube.name,
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
def test_export_to_luks_device(qube: QubeWrapper, mock_usb_luks_device: dict[str, str]) -> None:
    partition = mock_usb_luks_device["partition"]
    passphrase = mock_usb_luks_device["passphrase"]
    content = "SecureDrop export test"

    assert _export(qube, passphrase, content) == "SUCCESS_EXPORT"

    # Export leaves the device locked: unlock it to check the exported file
    cleartext = _udisks_call(qube, partition, "Encrypted.Unlock", f"'{passphrase}'", "{}")
    mountpoint = _udisks_call(qube, cleartext, "Filesystem.Mount", "{}")
    exported_content = qube.run(f"cat {shlex.quote(mountpoint)}/sd-export-*/export_data/test.txt")
    _udisks_call(qube, cleartext, "Filesystem.Unmount", "{}")
    _udisks_call(qube, partition, "Encrypted.Lock", "{}")
    assert exported_content == content


@pytest.mark.slow
@pytest.mark.configuration
@pytest.mark.run_alone  # Only one USB device can be attached for exporting
def test_export_to_luks_device_bad_passphrase(
    qube: QubeWrapper, mock_usb_luks_device: dict[str, str]
) -> None:
    assert _export(qube, "wrong-passphrase", "test") == "ERROR_UNLOCK_LUKS"
