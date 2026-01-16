"""
Integration tests for validating SecureDrop Workstation config,
specifically for the "sd-viewer" VM and related functionality.
"""

import subprocess

import pytest
from qubesadmin import Qubes

from tests.base import (
    SD_TAG,
    SD_TEMPLATE_LARGE,
    QubeWrapper,
)
from tests.base import (
    Test_SD_VM_Common as Test_SD_Viewer_Common,  # noqa: F401 [HACK: import so base tests run]
)


def _create_test_qube(dispvm_template_name):
    """
    Provision and boot a DispVM to target with integration tests.
    We don't want to test `sd-viewer`, because that's an AppVM;
    rather, we want to ensure that a DispVM based on that AppVM
    is configured correctly.
    """
    # VM was running and needs a restart to test on the latest version
    if dispvm_template_name in Qubes().domains:
        _shutdown_test_qube(dispvm_template_name)

    # Create disposable based on specified template
    qube_name = f"{dispvm_template_name}-disposable"
    cmd_create_disp = (
        f"qvm-create --disp --property auto_cleanup=True "
        f"--template {dispvm_template_name} {qube_name}"
    )
    subprocess.run(cmd_create_disp.split(), check=True)

    return qube_name


def _shutdown_test_qube(qube_name):
    """
    Gracefully power off the DispVM created for testing.
    """
    subprocess.run(["qvm-shutdown", "--wait", qube_name], check=True)


@pytest.fixture(scope="module")
def qube():
    """
    Handles the creation of disposable qubes based on the provided DVM template.
    Written as a fixture, so that the test suite handles both creation during
    loading of the test module, via yield, and cleanup after the execution of
    all tests in the module, via the post-yield teardown logic.
    """
    temp_qube_name = _create_test_qube("sd-viewer")

    yield QubeWrapper(
        temp_qube_name,
        expected_config_keys={"SD_MIME_HANDLING"},
        # this is not a comprehensive list, just a few that users are likely to use
        enforced_apparmor_profiles={
            "/usr/bin/evince",
            "/usr/bin/evince-previewer",
            "/usr/bin/evince-previewer//sanitized_helper",
            "/usr/bin/evince-thumbnailer",
            "/usr/bin/totem",
            "/usr/bin/totem-audio-preview",
            "/usr/bin/totem-video-thumbnailer",
            "/usr/bin/totem//sanitized_helper",
        },
        mime_types_handling=True,
        mime_vars_vm_name="sd-viewer",
    )

    # Tear Down
    _shutdown_test_qube(temp_qube_name)


@pytest.mark.packages
@pytest.mark.configuration
def test_sd_viewer_metapackage_installed(qube):
    assert qube.package_is_installed("securedrop-workstation-viewer")
    assert not qube.package_is_installed("securedrop-workstation-svs-disp")


@pytest.mark.configuration
@pytest.mark.packages
def test_sd_viewer_evince_installed(qube):
    pkg = "evince"
    assert qube.package_is_installed(pkg)


@pytest.mark.configuration
@pytest.mark.packages
def test_sd_viewer_libreoffice_installed(qube):
    assert qube.package_is_installed("libreoffice")


@pytest.mark.configuration
@pytest.mark.packages
def test_logging_configured(qube):
    qube.logging_configured()


@pytest.mark.configuration
@pytest.mark.packages
def test_redis_packages_not_installed(qube):
    """
    Only the log collector, i.e. sd-log, needs redis, so redis will be
    present in small template, but not in large.
    """
    assert not qube.package_is_installed("redis")
    assert not qube.package_is_installed("redis-server")


@pytest.mark.configuration
def test_mimetypes_service(qube):
    qube.service_is_active("securedrop-mime-handling")


@pytest.mark.configuration
def test_mailcap_hardened(qube):
    qube.mailcap_hardened()


@pytest.mark.configuration
def test_mimetypes_symlink(qube):
    assert qube.fileExists(".local/share/applications/mimeapps.list")
    symlink_location = qube.get_symlink_location(".local/share/applications/mimeapps.list")
    assert symlink_location == "/opt/sdw/mimeapps.list.sd-viewer"


@pytest.mark.provisioning
def test_sd_viewer_config(all_vms, config):
    """
    Confirm that qvm-prefs match expectations for the "sd-viewer" VM.
    """
    vm = all_vms["sd-viewer"]
    nvm = vm.netvm
    assert nvm is None
    assert vm.template.name == SD_TEMPLATE_LARGE
    assert not vm.provides_network
    assert vm.template_for_dispvms
    assert SD_TAG in vm.tags

    # MIME handling
    assert vm.features["service.securedrop-mime-handling"] == "1"
    assert vm.features["vm-config.SD_MIME_HANDLING"] == "sd-viewer"

    # VM will be marked "internal" only in prod context.
    if config["environment"] == "prod":
        assert vm.features.get("internal") == "1"
