import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Any

MANAGED_CONFIG_PATH = Path("/etc/securedrop/tor-browser.json")
MANAGED_BY = "SecureDrop Workstation"
SIGNING_KEY_FINGERPRINT = "EF6E286DDA85EA2A4BA7DE684E2C6E8793298290"
ONION_AUTH_FILENAME = "app-journalist.auth_private"
ONION_AUTH_PATTERN = re.compile(
    r"[a-z2-7]{56}\.onion:descriptor:x25519:[A-Z2-7]{52}\n?"
)
VERSION_PATTERN = re.compile(r"[0-9]+(?:\.[0-9]+){1,3}")


class ManagedConfigurationError(Exception):
    """The Workstation-managed launcher configuration cannot be used."""


def sha256_file(path: Path) -> str:
    """Return a local managed asset's digest without invoking external programs."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _administrator_error(prerequisite: str, detail: str) -> ManagedConfigurationError:
    return ManagedConfigurationError(
        f"The {prerequisite} {detail}. "
        "Ask your administrator to reapply the SecureDrop Admin configuration."
    )


def _required_string(config: dict[str, Any], name: str) -> str:
    value = config.get(name)
    if not isinstance(value, str) or not value:
        raise _administrator_error("managed configuration", f"has an invalid {name}")
    return value


def _validate_onion_auth(config: dict[str, Any]) -> None:
    credential_dir = Path(_required_string(config, "onion_auth_dir"))
    try:
        credentials = list(credential_dir.glob("*.auth_private"))
    except OSError as exc:
        raise _administrator_error("onion-auth credential", "cannot be inspected") from exc
    if not credentials:
        raise _administrator_error("onion-auth credential", "is missing")
    if len(credentials) != 1 or credentials[0].name != ONION_AUTH_FILENAME:
        raise _administrator_error(
            "onion-auth credential directory", "must contain exactly one supported credential"
        )

    credential = credentials[0]
    try:
        mode = stat.S_IMODE(credential.stat().st_mode)
        contents = credential.read_text()
    except OSError as exc:
        raise _administrator_error("onion-auth credential", "cannot be read") from exc
    if mode != 0o600:
        raise _administrator_error("onion-auth credential permissions", "must be 0600")
    if ONION_AUTH_PATTERN.fullmatch(contents) is None:
        raise _administrator_error("onion-auth credential", "is malformed")


def _validate_pinned_file(
    config: dict[str, Any], path_name: str, digest_name: str, description: str
) -> None:
    path = Path(_required_string(config, path_name))
    expected_digest = _required_string(config, digest_name)
    try:
        actual_digest = sha256_file(path)
    except OSError as exc:
        raise _administrator_error(description, "is missing or unreadable") from exc
    if not re.fullmatch(r"[0-9a-f]{64}", expected_digest) or actual_digest != expected_digest:
        raise _administrator_error(description, "does not match the Workstation-managed copy")


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

    minimum_version = _required_string(config, "minimum_version")
    if VERSION_PATTERN.fullmatch(minimum_version) is None:
        raise _administrator_error("release-managed minimum version", "is invalid")
    _validate_pinned_file(
        config,
        "minimum_version_path",
        "minimum_version_sha256",
        "release-managed minimum version",
    )
    try:
        installed_minimum_version = Path(
            _required_string(config, "minimum_version_path")
        ).read_text().strip()
    except OSError as exc:
        raise _administrator_error("release-managed minimum version", "cannot be read") from exc
    if installed_minimum_version != minimum_version:
        raise _administrator_error(
            "release-managed minimum version", "does not match the managed configuration"
        )
    fingerprint = _required_string(config, "signing_key_fingerprint")
    if fingerprint != SIGNING_KEY_FINGERPRINT:
        raise _administrator_error("Tor Browser signing key", "has an unexpected fingerprint")

    _validate_onion_auth(config)
    _validate_pinned_file(config, "torrc_path", "torrc_sha256", "managed Tor configuration")
    _validate_pinned_file(
        config, "signing_key_path", "signing_key_sha256", "Tor Browser signing key"
    )
    return config
