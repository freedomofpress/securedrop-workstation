"""
Integration tests for validating SecureDrop Workstation config,
specifically for the "sd-app" VM and related functionality.
"""

import pytest

from tests.base import (
    SD_TAG,
    SD_TEMPLATE_SMALL,
    QubeWrapper,
    get_mimeapp_vars_for_vm,
)
from tests.base import (
    Test_SD_VM_Common as Test_SD_App_Common,  # noqa: F401 [HACK: import so base tests run]
)


@pytest.fixture(scope="module")
def qube():
    return QubeWrapper(
        "sd-app",
        expected_config_keys={
            "QUBES_GPG_DOMAIN",
            "SD_SUBMISSION_KEY_FPR",
            "SD_MIME_HANDLING",
        },
        enforced_apparmor_profiles={
            "/usr/bin/securedrop-client",
        },
    )


@pytest.mark.configuration
def test_open_in_dvm_desktop(qube):
    contents = qube.get_file_contents("/usr/share/applications/open-in-dvm.desktop")
    expected_contents = [
        "TryExec=/usr/bin/qvm-open-in-vm",
        "Exec=/usr/bin/qvm-open-in-vm --view-only @dispvm:sd-viewer %f",
    ]
    for line in expected_contents:
        assert line in contents


SD_APP_MIME_TYPE_VARS = get_mimeapp_vars_for_vm("sd-app")


@pytest.mark.parametrize(("mime_type", "expected_app"), SD_APP_MIME_TYPE_VARS)
@pytest.mark.mime
@pytest.mark.slow
@pytest.mark.configuration
def test_mime_types(mime_type, expected_app, qube):
    """
    Functionally verifies that the VM config handles specific filetypes correctly,
    opening them with the appropriate program.
    """
    actual_app = qube.run(f"xdg-mime query default {mime_type}")
    # All associations should lead to open-in-dvm!
    assert expected_app == "open-in-dvm.desktop"
    assert actual_app == expected_app


@pytest.mark.configuration
def test_mailcap_hardened(qube):
    qube.mailcap_hardened()


@pytest.mark.configuration
def test_sd_client_package_installed(qube):
    assert qube.package_is_installed("securedrop-client")


@pytest.mark.configuration
def test_sd_client_dependencies_installed(qube):
    assert qube.package_is_installed("python3-pyqt5")
    assert qube.package_is_installed("python3-pyqt5.qtsvg")


@pytest.mark.provisioning
def test_sd_client_config(dom0_config, qube):
    assert dom0_config["submission_key_fpr"] == qube.vm_config_read("SD_SUBMISSION_KEY_FPR")


@pytest.mark.provisioning
def test_logging_configured(qube):
    qube.logging_configured()


def test_sd_app_config(config, qube, all_vms):
    vm = all_vms["sd-app"]
    nvm = vm.netvm
    assert nvm is None
    assert vm.template.name == SD_TEMPLATE_SMALL
    assert not vm.provides_network
    assert not vm.template_for_dispvms
    assert "service.securedrop-log-server" not in vm.features
    assert SD_TAG in vm.tags
    assert "sd-client" in vm.tags
    # Check the size of the private volume
    # Should be 10GB
    # >>> 1024 * 1024 * 10 * 1024
    size = config["vmsizes"]["sd_app"]
    vol = vm.volumes["private"]
    assert vol.size == size * 1024 * 1024 * 1024

    # MIME handling
    assert vm.features["service.securedrop-mime-handling"] == "1"
    assert vm.features["vm-config.SD_MIME_HANDLING"] == "sd-app"
    assert qube.service_is_active("securedrop-mime-handling")

    # Arti should *not* be running
    assert not qube.service_is_active("securedrop-arti")
