import pytest
from qubesadmin.app import VMCollection

from tests.markers import needs_admin

pytestmark = needs_admin


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
