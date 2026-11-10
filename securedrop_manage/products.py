"""
Detection of which SecureDrop products are installed in dom0.

This module is shared with the updater, so it must not import qubesadmin or
other dom0-only dependencies.
"""

from enum import Enum
from pathlib import Path

PRODUCTS_PATH = Path("/usr/share/securedrop/products/")


class NoProductInstalledError(Exception):
    pass


class Product(Enum):
    JOURNALIST = "journalist"
    ADMIN = "admin"
    ALL = "all"

    @property
    def contains_journalist(self) -> bool:
        return self in (Product.JOURNALIST, Product.ALL)

    @property
    def contains_admin(self) -> bool:
        return self in (Product.ADMIN, Product.ALL)

    def __str__(self) -> str:
        """needed for nice --help output"""
        return self.value

    def as_text(self) -> str:
        match self:
            case Product.JOURNALIST:
                return "Journalist Workstation"
            case Product.ADMIN:
                return "Admin Workstation"
            case Product.ALL:
                return "SecureDrop Workstation"

    @property
    def tag(self) -> str:
        match self:
            case Product.JOURNALIST:
                return "sd-journalist"
            case Product.ADMIN:
                return "sd-admin"
            case Product.ALL:
                return "sd-workstation"

    @property
    def top(self) -> str:
        match self:
            case Product.JOURNALIST:
                return "securedrop_salt/sd-workstation.top"
            case Product.ADMIN:
                return "admin_salt/sd-admin.top"
            case Product.ALL:
                return "top.sls"  # Merges enabled top files (state.highstate equivalent)


def get_installed_product(products_path: Path = PRODUCTS_PATH) -> Product:
    journalist = (products_path / "journalist-workstation.json").is_file()
    admin = (products_path / "admin-workstation.json").is_file()
    if journalist and admin:
        return Product.ALL
    if journalist:
        return Product.JOURNALIST
    if admin:
        return Product.ADMIN
    raise NoProductInstalledError(f"No SecureDrop products are installed (checked {products_path})")
