import json
from pathlib import Path
from typing import Any

MANAGED_CONFIG_PATH = Path("/etc/securedrop/tor-browser.json")
MANAGED_BY = "SecureDrop Workstation"


class ManagedConfigurationError(Exception):
    """The Workstation-managed launcher configuration cannot be used."""


def load_managed_config() -> dict[str, Any]:
    """Load the local configuration before any external activity is allowed."""
    try:
        config = json.loads(MANAGED_CONFIG_PATH.read_text())
    except FileNotFoundError as exc:
        raise ManagedConfigurationError(
            f"The Workstation-managed configuration is missing at {MANAGED_CONFIG_PATH}. "
            "Ask your administrator to reapply the SecureDrop Admin configuration."
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ManagedConfigurationError(
            f"The Workstation-managed configuration at {MANAGED_CONFIG_PATH} cannot be read. "
            "Ask your administrator to reapply the SecureDrop Admin configuration."
        ) from exc

    if not isinstance(config, dict) or config.get("managed_by") != MANAGED_BY:
        raise ManagedConfigurationError(
            f"The Workstation-managed configuration at {MANAGED_CONFIG_PATH} is invalid. "
            "Ask your administrator to reapply the SecureDrop Admin configuration."
        )
    return config
