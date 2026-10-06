from enum import Enum
from pathlib import Path

CONFIG_PATH = Path.home() / ".config/securedrop-manage"
LEGACY_CONFIG_PATH = Path("/usr/share/securedrop-workstation-dom0-config/")

# Files expected in CONFIG_PATH
CONFIG_FILENAME = "config.json"
SUBMISSION_KEY_FILENAME = "sd-journalist.sec"


class ManageException(Exception):
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
