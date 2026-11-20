from pathlib import Path

import pytest
from qubesadmin.app import VMCollection

from securedrop_manage import products
from tests.base import is_managed_qube


def test_get_installed_product(tmp_path: Path) -> None:
    with pytest.raises(products.NoProductInstalledError):
        # nothing installed in our tmp_path yet
        products.get_installed_product(tmp_path)

    (tmp_path / "admin-workstation.json").write_text("{}")
    assert products.get_installed_product(tmp_path) is products.Product.ADMIN

    (tmp_path / "journalist-workstation.json").write_text("{}")
    assert products.get_installed_product(tmp_path) is products.Product.ALL

    (tmp_path / "admin-workstation.json").unlink()
    assert products.get_installed_product(tmp_path) is products.Product.JOURNALIST


def test_product_tags(all_vms: VMCollection) -> None:
    """
    Checks that product's tags are disjoint, but also share a common tag
    """
    from collections import defaultdict

    vms_by_tag = defaultdict(set)
    for vm in all_vms:
        for tag in vm.tags:
            if is_managed_qube(vm):
                vms_by_tag[tag].add(vm)

    product_journalist_vms = vms_by_tag[products.Product.JOURNALIST.tag]
    product_admin_vms = vms_by_tag[products.Product.ADMIN.tag]
    product_all_vms = vms_by_tag[products.Product.ALL.tag]

    # No overlap between admin and journalist workstations
    assert product_journalist_vms.isdisjoint(product_admin_vms)

    # VM in either is always tagged with a shared workstation tag
    assert product_all_vms == product_journalist_vms.union(product_admin_vms)
