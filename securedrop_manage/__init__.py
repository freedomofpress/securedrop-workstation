from pathlib import Path

CONFIG_PATH = Path.home() / ".config/securedrop-manage"
LEGACY_CONFIG_PATH = Path("/usr/share/securedrop-workstation-dom0-config/")

# Files expected in CONFIG_PATH
CONFIG_FILENAME = "config.json"
SUBMISSION_KEY_FILENAME = "sd-journalist.sec"


class ManageException(Exception):
    pass
