import pytest
from qubesadmin.app import VMCollection

from securedrop_manage import main as manage
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
    assert favorites == manage.ADMIN_DOM0_MENU_FEATURES["menu-favorites"]
    # No favorites on the qubes themselves, which would bypass sdw-updater
    for vm in ("sd-admin", "sd-admin-vault"):
        assert not all_vms[vm].features.get("menu-favorites")
