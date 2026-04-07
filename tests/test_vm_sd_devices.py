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

# NOTE: this file needs includes tests for the functionally similar 'sd-devices'
# and 'sd-printers'. Some tests overlap (tested on both through the 'qube' fixture)
# and some only happen in one VM. In this last case dedicated qube fixtures are used
_qubes = {
    "sd-devices": QubeWrapper(
        "sd-devices",
        expected_config_keys={"SD_MIME_HANDLING"},
        mime_types_handling=True,
        devices_attachable=True,
    ),
    "sd-printers": QubeWrapper(
        "sd-printers",
        expected_config_keys={"SD_MIME_HANDLING"},
        mime_types_handling=True,
        mime_vars_vm_name="sd-devices",  # MIME-wise it behaves similarly
        devices_attachable=True,
    ),
}


@pytest.fixture(scope="module")
def qube_sd_devices():
    return _qubes["sd-devices"]


@pytest.fixture(scope="module")
def qube_sd_printers():
    return _qubes["sd-printers"]


# Parameterize: tests calling this fixture will run for each qube
@pytest.fixture(scope="module", params=_qubes.values(), ids=_qubes.keys())
def qube(request):
    return request.param  # returns a fixture for each qube


def test_files_are_properly_copied(qube):
    assert qube.fileExists("/usr/bin/send-to-usb")
    assert qube.fileExists("/usr/share/applications/send-to-usb.desktop")
    assert qube.fileExists("/usr/share/mime/packages/application-x-sd-export.xml")


def test_sd_export_package_installed(qube_sd_devices):
    assert qube_sd_devices.package_is_installed("udisks2")
    assert qube_sd_devices.package_is_installed("securedrop-export")
    assert qube_sd_devices.package_is_installed("gnome-disk-utility")


def test_logging_configured(qube):
    qube.logging_configured()


def test_mailcap_hardened(qube):
    qube.mailcap_hardened()


def test_open_in_dvm_desktop(qube_sd_devices):
    contents = qube_sd_devices.get_file_contents("/usr/share/applications/open-in-dvm.desktop")
    expected_contents = [
        "TryExec=/usr/bin/qvm-open-in-vm",
        "Exec=/usr/bin/qvm-open-in-vm --view-only @dispvm:sd-viewer %f",
    ]
    for line in expected_contents:
        assert line in contents


def test_sd_printers_config(qube_sd_printers):
    """
    Confirm that qvm-prefs match expectations for this VM.
    """
    vm = qube_sd_printers.vm
    nvm = vm.netvm
    assert nvm is None
    vm_type = vm.klass
    assert vm_type == "DispVM"
    assert SD_TAG in vm.tags

    assert vm.features["service.avahi"] == "1"
    assert vm.features["service.cups"] == "1"

    # MIME handling
    assert vm.features["service.securedrop-mime-handling"] == "1"
    assert vm.features["vm-config.SD_MIME_HANDLING"] == "sd-devices"
    assert qube_sd_printers.service_is_active("securedrop-mime-handling")


def test_sd_devices_config(qube_sd_devices):
    """
    Confirm that qvm-prefs match expectations for this VM.
    """
    vm = qube_sd_devices.vm
    nvm = vm.netvm
    assert nvm is None
    vm_type = vm.klass
    assert vm_type == "DispVM"
    assert SD_TAG in vm.tags

    # NOTE: earlier versions had this enabled (before 'sd-printers' introduced)
    assert "service.avahi" not in vm.features

    # MIME handling
    assert vm.features["service.securedrop-mime-handling"] == "1"
    assert vm.features["vm-config.SD_MIME_HANDLING"] == "sd-devices"
    assert qube_sd_devices.service_is_active("securedrop-mime-handling")


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

    # NOTE: earlier versions had this enabled
    assert "service.avahi" not in vm.features
    assert "service.cups" not in vm.features

    # MIME handling (dvm does NOT setup mime, only its disposables do)
    assert "service.securedrop-mime-handling" not in vm.features
    assert not dvm_qube.service_is_active("securedrop-mime-handling")
