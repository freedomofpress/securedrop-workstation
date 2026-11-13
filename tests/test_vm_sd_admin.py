import pytest
from qubesadmin.app import VMCollection

from tests.markers import needs_admin

pytestmark = needs_admin

SD_ADMIN_FAVORITES = {
    "press.freedom.SecureDropJournalistInterface",
    "press.freedom.SecureDropSourceInterface",
    "press.freedom.SecureDropSshApp",
    "press.freedom.SecureDropSshMon",
}


@pytest.mark.provisioning
def test_app_menu_opens_to_favorites(all_vms: VMCollection) -> None:
    assert all_vms["dom0"].features.get("menu-initial-page") == "favorites_page"


@pytest.mark.provisioning
def test_sd_admin_menu_favorites(all_vms: VMCollection) -> None:
    """
    Favorites are read from the qube that owns the app, and matched against
    X-Qubes-AppName (the desktop file name without ".desktop").
    """
    favorites = set(all_vms["sd-admin"].features.get("menu-favorites", "").split())
    assert favorites == SD_ADMIN_FAVORITES


@pytest.mark.provisioning
def test_sd_admin_vault_menu_favorites(all_vms: VMCollection) -> None:
    """
    KeePassXC runs in sd-admin-vault, so its favorite must be set there.
    """
    vm = all_vms["sd-admin-vault"]
    assert vm.features.get("menu-items") == "org.keepassxc.KeePassXC.desktop"
    assert vm.features.get("menu-favorites") == "org.keepassxc.KeePassXC"
