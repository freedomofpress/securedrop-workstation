"""
Integration tests for validating SecureDrop Workstation config,
specifically for the "sd-proxy" VM and related functionality.
"""

import pytest

from tests.base import (
    QubeWrapper,
)
from tests.base import (
    Test_SD_VM_Common as Test_SD_Proxy_Common,  # noqa: F401 [HACK: import so base tests run]
)


@pytest.fixture(scope="module")
def qube():
    return QubeWrapper(
        "sd-proxy",
        expected_config_keys={"SD_PROXY_ORIGIN", "SD_PROXY_ORIGIN_KEY", "SD_MIME_HANDLING"},
        enforced_apparmor_profiles={"/usr/bin/securedrop-proxy"},
    )


def test_do_not_open_here(qube):
    """
    The do-not-open here script has been removed from sd-proxy.
    All VMs now default to using open-in-dvm.
    """
    assert not qube.fileExists("/usr/bin/do-not-open-here")


def test_sd_proxy_package_installed(qube):
    assert qube.package_is_installed("securedrop-proxy")


def test_tor_hidserv_auth_url(qube, dom0_config):
    assert f"http://{dom0_config['hidserv']['hostname']}" == qube.vm_config_read("SD_PROXY_ORIGIN")


def test_whonix_ws_repo_absent(qube):
    """
    The sd-proxy VM was previously based on Whonix Workstation,
    but we've since moved to the standard SDW Debian-based template.
    Guard against regressions by ensuring the old Whonix apt list
    is missing.
    """
    # Whonix project changed the repo filename ~2021-05, so check both.
    assert not qube.fileExists("/etc/apt/sources.list.d/whonix.list")
    assert not qube.fileExists("/etc/apt/sources.list.d/derivative.list")


def test_logging_configured(qube):
    qube.logging_configured()


def test_mimeapps(qube):
    results = qube.run("cat /usr/share/applications/mimeapps.list")
    for line in results.splitlines():
        if line.startswith(("#", "[Default")):
            # Skip comments and the leading [Default Applications]
            continue
        mime, target = line.split("=", 1)
        assert target == "open-in-dvm.desktop;"
        # Now functionally test it
        actual_app = qube.run(f"xdg-mime query default {mime}")
        assert actual_app == "open-in-dvm.desktop"


def test_mailcap_hardened(qube):
    qube.mailcap_hardened()


def test_sd_proxy_config(qube):
    """
    Confirm that qvm-prefs for the VM match expectations.
    """
    vm = qube
    assert vm.template.name == "sd-proxy-dvm"
    assert vm.klass == "DispVM"
    assert vm.netvm.name == "sys-firewall"
    assert vm.autostart
    assert not vm.provides_network
    assert vm.default_dispvm is None
    assert SD_TAG in vm.tags
    assert vm.features["service.securedrop-mime-handling"] == "1"
    assert vm.features["service.securedrop-arti"] == "1"
    assert vm.features["vm-config.SD_MIME_HANDLING"] == "default"
    assert vm.check_service_running("securedrop-mime-handling")
    assert vm.check_service_running("securedrop-proxy-onion-config")
    assert vm.check_service_running("tor")
