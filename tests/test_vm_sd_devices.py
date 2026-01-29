"""
Integration tests for validating SecureDrop Workstation config,
specifically for the "sd-devices" VM and related functionality.
"""

import pytest

from tests.base import (
    SD_TAG,
    QubeWrapper,
)
from tests.base import (
    Test_SD_VM_Common as Test_SD_Devices_Common,  # noqa: F401 [HACK: import so base tests run]
)


@pytest.fixture(scope="module")
def qube():
    return QubeWrapper(
        "sd-devices",
        expected_config_keys={"SD_MIME_HANDLING"},
        mime_types_handling=True,
        devices_attachable=True,
    )


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


def test_sd_devices_config(qube, all_vms):
    """
    Confirm that qvm-prefs match expectations for this VM.
    """
    vm = all_vms["sd-devices"]
    nvm = vm.netvm
    assert nvm is None
    vm_type = vm.klass
    assert vm_type == "DispVM"
    assert SD_TAG in vm.tags

    assert vm.features["service.avahi"] == "1"

    # MIME handling
    assert vm.features["service.securedrop-mime-handling"] == "1"
    assert vm.features["vm-config.SD_MIME_HANDLING"] == "sd-devices"
    assert qube.service_is_active("securedrop-mime-handling")


def test_sd_devices_dvm_config(all_vms):
    """
    Confirm that qvm-prefs match expectations for the sd-devices DispVM
    """
    # N.B. Don't use fixture, which is hardcoded for "sd-devices" VM.
    dvm_qube = QubeWrapper("sd-devices-dvm")
    vm = all_vms[dvm_qube.name]
    nvm = vm.netvm
    assert nvm is None
    assert SD_TAG in vm.tags
    assert vm.template_for_dispvms

    assert "service.avahi" not in vm.features
    # MIME handling (dvm does NOT setup mime, only its disposables do)
    assert "service.securedrop-mime-handling" not in vm.features
    assert not dvm_qube.service_is_active("securedrop-mime-handling")
