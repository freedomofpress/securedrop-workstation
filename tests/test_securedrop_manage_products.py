from pathlib import Path

import pytest

from securedrop_manage import products


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
