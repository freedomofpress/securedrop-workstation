"""
Integration tests for the "sd-admin" VM.
"""

import pytest
from qubesadmin.app import VMCollection

from tests.base import SD_ADMIN_TEMPLATE, SD_TAG, QubeWrapper
from tests.base import (
    Test_SD_VM_Common as Test_SD_Admin_Common,  # noqa: F401 [HACK: import so base tests run]
)
from tests.markers import needs_admin
from tests.mock_usb import assert_usb_qrexec_denied

pytestmark = needs_admin


@pytest.fixture(scope="module")
def qube() -> QubeWrapper:
    return QubeWrapper("sd-admin")


@pytest.mark.provisioning
def test_sd_admin_config(all_vms: VMCollection) -> None:
    """
    Confirm that qvm-prefs match expectations for the sd-admin VM.
    """
    vm = all_vms["sd-admin"]
    assert vm.klass == "AppVM"
    assert vm.netvm is not None
    assert vm.netvm.name == "sys-firewall"
    assert vm.template.name == SD_ADMIN_TEMPLATE
    assert vm.default_dispvm is None
    assert not vm.autostart
    assert not vm.provides_network
    assert not vm.template_for_dispvms
    assert vm.features["service.paxctld"] == "1"
    assert SD_TAG in vm.tags
    assert "sd-admin" in vm.tags


@pytest.mark.provisioning
def test_sd_admin_template_config(all_vms: VMCollection) -> None:
    """
    Confirm that qvm-prefs match expectations for the sd-admin template.
    """
    vm = all_vms[SD_ADMIN_TEMPLATE]
    assert vm.klass == "TemplateVM"
    assert vm.default_dispvm is None
    assert SD_TAG in vm.tags
    assert "sd-admin" in vm.tags
    assert "sd-updater" in vm.tags


@pytest.mark.configuration
def test_sd_admin_packages_installed(qube: QubeWrapper) -> None:
    assert qube.package_is_installed("securedrop-admin-qubes")


@pytest.mark.provisioning
def test_app_menu_opens_to_favorites(all_vms: VMCollection) -> None:
    assert all_vms["dom0"].features.get("menu-initial-page") == "favorites_page"


@pytest.mark.provisioning
def test_admin_menu_favorites(all_vms: VMCollection) -> None:
    """
    Favorites point at the dom0 launchers, so apps start via sdw-updater.
    For dom0 apps the menu matches against the full .desktop file name.
    """
    favorites = all_vms["dom0"].features.get("menu-favorites", "")
    assert favorites.split() == [
        "press.freedom.SecureDropAdminKeePassXC.desktop",
        "press.freedom.SecureDropJournalistInterface.desktop",
        "press.freedom.SecureDropSourceInterface.desktop",
        "press.freedom.SecureDropSshApp.desktop",
        "press.freedom.SecureDropSshMon.desktop",
    ]
    # No favorites on the qubes themselves, which would bypass sdw-updater
    for vm in all_vms:
        if vm.name != "dom0":
            assert not vm.features.get("menu-favorites"), vm.name


def test_sd_admin_usb_attach_arbitrary_device_denied(qube: QubeWrapper) -> None:
    assert_usb_qrexec_denied(qube)
