"""
Helpers for tests that plug a mock USB mass storage device into sys-usb and
use it from the qube it gets attached to.
"""

import os
import re
import shlex
import subprocess
import time
from types import SimpleNamespace
from typing import Any

import pytest

from tests.base import QubeWrapper

IS_CI = os.environ.get("CI") == "true"

# Seconds to wait for a udisks2 call: LUKS formatting can take longer than
# gdbus' default 25s, especially on slower CI hardware
UDISKS_TIMEOUT = 300 if IS_CI else 45

# Unmounts and closes anything left on USB disks in a qube (e.g. by a test
# that failed midway), so the device can be removed cleanly
CLOSE_USB_DISKS = (
    "for disk in $(lsblk -dnpo NAME,TRAN | awk '$2 == \"usb\" {print $1}'); do"
    " lsblk -nrpo NAME,MOUNTPOINT $disk | awk '$2 != \"\" {print $1}' | xargs -r umount;"
    " lsblk -nrpo NAME,TYPE $disk | awk '$2 == \"crypt\" {print $1}' | xargs -r dmsetup remove;"
    " done; udevadm settle"
)


def udisks_call(qube: QubeWrapper, object_path: str, method: str, *args: str) -> str:
    """
    Call a udisks2 D-Bus method as the desktop user (as GNOME Disks does) and
    return its result (an object path or a mount point), if any
    """
    output = qube.run(
        f"gdbus call --system --timeout {UDISKS_TIMEOUT} --dest org.freedesktop.UDisks2 "
        f"--object-path {object_path} --method org.freedesktop.UDisks2.{method} "
        f"{shlex.join(args)}"
    )

    # gdbus prints e.g. "(objectpath '/org/.../sda1',)", "('/media/...',)" or "()"
    match = re.search(r"'(.*)'", output)
    return match.group(1) if match else ""


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
        """Adapt vm.run() to return the USB Tests' modified version"""
        try:
            out, err = self.vm.run(command, user="root")
            ret = 0
        except subprocess.CalledProcessError as error:
            out, err = error.stdout, error.stderr
            ret = error.returncode
        return SimpleNamespace(returncode=ret, communicate=lambda: (out, err))


def create_usb_gadget(qube_sys_usb: QubeWrapper) -> str:
    """
    Creates a USB mass storage device in sys-usb and returns its qvm-usb port
    (e.g. "sys-usb:2-1").

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

    # The gadget is the only device on the dummy host controller
    port = qube_sys_usb.run(
        "ls /sys/bus/platform/devices/dummy_hcd.0/usb*/ | grep -x '[0-9]*-[0-9]*'"
    )
    return f"{qube_sys_usb.name}:{port}"


def remove_usb_gadget(qube_sys_usb: QubeWrapper) -> None:
    """Like usbproxy_tests.remove_usb_gadget(), which the adapter doesn't support"""
    qube_sys_usb.run("echo > /sys/kernel/config/usb_gadget/test_g1/UDC", user="root")


def wait_for_usb_disk(qube: QubeWrapper) -> str:
    """
    Waits for the mock USB device to show up in the qube it is attached to and
    returns its disk name there (e.g. "sda")
    """
    # Wait for the attachment to be seen by the kernel
    disk = ""
    patience = 60  # seconds
    while patience > 0 and not disk:
        disk = qube.run("lsblk -dno NAME,TRAN | awk '$2 == \"usb\" {print $1}'")
        time.sleep(1)
        patience -= 1
    assert disk, f"USB device was not attached to {qube.name}"

    # Wait for detection by udisks2, which happens a bit later
    while patience > 0 and not udisks_call(
        qube,
        "/org/freedesktop/UDisks2/Manager",
        "Manager.ResolveDevice",
        f"{{'path': <'/dev/{disk}'>}}",
        "{}",
    ):
        time.sleep(1)
        patience -= 1
    assert patience > 0, f"USB device was not detected by udisks2 in {qube.name}"
    return disk


def close_usb_disks(qube: QubeWrapper) -> None:
    qube.run(CLOSE_USB_DISKS, user="root")


def format_luks(qube: QubeWrapper, disk: str) -> dict[str, str]:
    """
    Formats the mock USB device with LUKS + ext4.

    The formatting follows the Transfer Device docs (GNOME Disks → Format
    Partition… → "Password protect volume (LUKS)" + Ext4), done through the
    same udisks2 calls GNOME Disks makes. The volume is left locked.
    https://docs.securedrop.org/en/stable/admin/installation/set_up_transfer_and_export_device.html
    """
    passphrase = "correct-horse-battery-staple"

    block_path = f"/org/freedesktop/UDisks2/block_devices/{disk}"
    udisks_call(qube, block_path, "Block.Format", "'gpt'", "{}")
    partition = udisks_call(
        qube, block_path, "PartitionTable.CreatePartition", "0", "0", "''", "''", "{}"
    )
    udisks_call(
        qube,
        partition,
        "Block.Format",
        "'ext4'",
        f"{{'label': <'Transfer Device'>, 'encrypt.passphrase': <'{passphrase}'>,"
        " 'take-ownership': <true>}",
    )
    # Formatting leaves it unlocked: lock it, like a freshly plugged-in device
    udisks_call(qube, partition, "Encrypted.Lock", "{}")

    return {"partition": partition, "passphrase": passphrase}
