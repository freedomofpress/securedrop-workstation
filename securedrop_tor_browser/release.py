"""Fail-closed discovery and rollback policy for Tor Browser releases."""

from __future__ import annotations

import http.client
import json
import os
import ssl
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import total_ordering
from pathlib import Path
from typing import IO, Protocol
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urljoin, urlsplit

METADATA_URL = (
    "https://aus1.torproject.org/torbrowser/update_3/release/" "download-linux-x86_64.json"
)
METADATA_HOSTS = frozenset({"aus1.torproject.org", "aus2.torproject.org"})
DOWNLOAD_HOSTS = frozenset({"dist.torproject.org"})
REQUEST_TIMEOUT_SECONDS = 15.0
MAX_METADATA_BYTES = 64 * 1024
READ_CHUNK_BYTES = 16 * 1024
MAX_REDIRECTS = 3
MAX_AUTOMATIC_RETRIES = 2
BACKOFF_SECONDS = (0.25, 0.5)
TRANSIENT_HTTP_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504})
DURABLE_STATE_ROOT = Path("/home/user/.local/share/securedrop-tor-browser")
STATE_ROOT = DURABLE_STATE_ROOT
BROWSER_PATH = STATE_ROOT / "browser"
INSTALLED_VERSION_PATH = BROWSER_PATH / ".securedrop-version"
HIGH_WATER_VERSION_PATH = STATE_ROOT / "highest-version"


class ReleaseError(Exception):
    """Base class for a release-discovery failure."""


class TransientReleaseError(ReleaseError):
    """Release metadata could not be retrieved due to a transient condition."""


class ReleaseSecurityError(ReleaseError):
    """Release metadata failed a security or integrity constraint."""


class ReleaseCancelled(ReleaseError):
    """The user cancelled release discovery."""


@total_ordering
class Version:
    """A strictly numeric Tor Browser version suitable for rollback comparisons."""

    def __init__(self, value: str) -> None:
        parts = value.split(".")
        if (
            len(parts) < 2
            or len(parts) > 4
            or any(not part.isascii() or not part.isdigit() for part in parts)
        ):
            raise ValueError(f"Invalid Tor Browser version: {value!r}")
        self.value = value
        self._parts = tuple(int(part) for part in parts)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._parts == other._parts

    def __lt__(self, other: Version) -> bool:
        return self._parts < other._parts

    def __hash__(self) -> int:
        return hash(self._parts)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Version({self.value!r})"


@dataclass(frozen=True)
class StableRelease:
    version: Version
    bundle_url: str
    signature_url: str


class ReleaseAction(Enum):
    CURRENT = "current"
    INSTALL = "install"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ReleaseDecision:
    action: ReleaseAction
    reason: str


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: dict[str, str]
    body: bytes


class Transport(Protocol):
    def __call__(self, url: str, timeout: float, cancelled: Callable[[], bool]) -> HttpResponse: ...


class _NoRedirectHandler(urllib_request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib_request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: http.client.HTTPMessage,
        newurl: str,
    ) -> None:
        """Return redirects to the policy layer instead of following them."""


def _check_cancelled(cancelled: Callable[[], bool]) -> None:
    if cancelled():
        raise ReleaseCancelled("Tor Browser release check was cancelled.")


def _validate_https_url(url: str, allowed_hosts: frozenset[str], description: str) -> None:
    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ReleaseSecurityError(f"The {description} URL has an invalid port.") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname not in allowed_hosts
        or port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ReleaseSecurityError(f"The {description} URL is not an approved Tor HTTPS location.")


def _declared_response_is_too_large(headers: dict[str, str]) -> bool:
    declared_length = headers.get("content-length")
    if declared_length is None:
        return False
    try:
        return int(declared_length) > MAX_METADATA_BYTES
    except ValueError as exc:
        raise ReleaseSecurityError("Tor Browser release metadata has an invalid length.") from exc


def _read_response(
    response: urllib_error.HTTPError | http.client.HTTPResponse,
    cancelled: Callable[[], bool],
) -> HttpResponse:
    headers = {name.lower(): value.strip() for name, value in response.headers.items()}
    if _declared_response_is_too_large(headers):
        raise ReleaseSecurityError("Tor Browser release metadata is too large.")

    body = bytearray()
    while len(body) <= MAX_METADATA_BYTES:
        _check_cancelled(cancelled)
        chunk = response.read(min(READ_CHUNK_BYTES, MAX_METADATA_BYTES + 1 - len(body)))
        _check_cancelled(cancelled)
        if not chunk:
            break
        body.extend(chunk)
    if len(body) > MAX_METADATA_BYTES:
        raise ReleaseSecurityError("Tor Browser release metadata is too large.")
    if response.status is None:
        raise ReleaseSecurityError("Tor Browser metadata response is malformed.")
    return HttpResponse(response.status, headers, bytes(body))


def _is_tls_failure(exc: BaseException) -> bool:
    if isinstance(exc, ssl.SSLError):
        return True
    return isinstance(exc, urllib_error.URLError) and isinstance(exc.reason, ssl.SSLError)


def _default_transport(url: str, timeout: float, cancelled: Callable[[], bool]) -> HttpResponse:
    """Make one bounded, non-redirecting HTTPS request from the admin AppVM."""
    _validate_https_url(url, METADATA_HOSTS, "metadata")
    _check_cancelled(cancelled)
    request = urllib_request.Request(  # noqa: S310 - URL is restricted above.
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "SecureDrop-Workstation-Tor-Browser-Updater",
        },
    )
    opener = urllib_request.build_opener(_NoRedirectHandler())
    try:
        try:
            response = opener.open(request, timeout=timeout)
        except urllib_error.HTTPError as exc:
            response = exc
        with response:
            return _read_response(response, cancelled)
    except ReleaseError:
        raise
    except (urllib_error.URLError, TimeoutError, OSError) as exc:
        if _is_tls_failure(exc):
            raise ReleaseSecurityError("Tor Browser metadata failed HTTPS validation.") from exc
        raise TransientReleaseError("Tor Browser release metadata is unavailable.") from exc
    except (http.client.HTTPException, ValueError) as exc:
        raise ReleaseSecurityError("Tor Browser metadata response is malformed.") from exc


def _fetch_metadata(transport: Transport, cancelled: Callable[[], bool]) -> bytes:
    url = METADATA_URL
    for redirect_count in range(MAX_REDIRECTS + 1):
        _check_cancelled(cancelled)
        _validate_https_url(url, METADATA_HOSTS, "metadata")
        response = transport(url, REQUEST_TIMEOUT_SECONDS, cancelled)

        if _declared_response_is_too_large(response.headers):
            raise ReleaseSecurityError("Tor Browser release metadata is too large.")
        if len(response.body) > MAX_METADATA_BYTES:
            raise ReleaseSecurityError("Tor Browser release metadata is too large.")

        if response.status in {301, 302, 303, 307, 308}:
            if redirect_count == MAX_REDIRECTS:
                raise ReleaseSecurityError("Tor Browser metadata redirected too many times.")
            location = response.headers.get("location")
            if not location:
                raise ReleaseSecurityError("Tor Browser metadata redirect is malformed.")
            url = urljoin(url, location)
            _validate_https_url(url, METADATA_HOSTS, "metadata redirect")
            continue
        if response.status in TRANSIENT_HTTP_STATUSES:
            raise TransientReleaseError("Tor Browser release metadata is unavailable.")
        if response.status != 200:
            raise ReleaseSecurityError(
                f"Tor Browser release metadata returned HTTP {response.status}."
            )
        return response.body
    raise AssertionError("unreachable")


def _parse_metadata(body: bytes) -> StableRelease:
    try:
        document = json.loads(body)
        if not isinstance(document, dict):
            raise ValueError
        version_value = document["version"]
        bundle_url = document["binary"]
        signature_url = document["sig"]
        if not all(isinstance(value, str) for value in (version_value, bundle_url, signature_url)):
            raise ValueError
        version = Version(version_value)
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ReleaseSecurityError("Tor Browser release metadata is malformed.") from exc

    _validate_https_url(bundle_url, DOWNLOAD_HOSTS, "bundle")
    _validate_https_url(signature_url, DOWNLOAD_HOSTS, "signature")
    expected_directory = f"/torbrowser/{version}/"
    if expected_directory not in urlsplit(bundle_url).path or signature_url != bundle_url + ".asc":
        raise ReleaseSecurityError(
            "Tor Browser release metadata does not consistently identify the release."
        )
    return StableRelease(version, bundle_url, signature_url)


def discover_stable_release(
    *,
    transport: Transport = _default_transport,
    sleep: Callable[[float], None] = time.sleep,
    cancelled: Callable[[], bool] = lambda: False,
) -> StableRelease:
    """Discover the current stable Linux release with bounded transient retries."""
    for attempt in range(MAX_AUTOMATIC_RETRIES + 1):
        try:
            return _parse_metadata(_fetch_metadata(transport, cancelled))
        except TransientReleaseError:
            if attempt == MAX_AUTOMATIC_RETRIES:
                raise
            _check_cancelled(cancelled)
            sleep(BACKOFF_SECONDS[attempt])
    raise AssertionError("unreachable")


def decide_release_action(
    advertised: Version,
    *,
    installed: Version | None,
    high_water: Version | None,
    minimum: Version,
) -> ReleaseDecision:
    """Apply freshness and rollback gates without changing any durable state."""
    floors = [minimum]
    if installed is not None:
        floors.append(installed)
    if high_water is not None:
        floors.append(high_water)
    required_floor = max(floors)
    if advertised < required_floor:
        return ReleaseDecision(
            ReleaseAction.BLOCKED,
            f"Advertised release {advertised} is below required version {required_floor}.",
        )
    if installed == advertised:
        return ReleaseDecision(ReleaseAction.CURRENT, "Installed Tor Browser is current.")
    return ReleaseDecision(ReleaseAction.INSTALL, f"Tor Browser {advertised} must be installed.")


def read_optional_version(path: Path) -> Version | None:
    """Read version state without creating or modifying it."""
    try:
        value = path.read_text().strip()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ReleaseSecurityError(f"Tor Browser version state at {path} is unreadable.") from exc
    try:
        return Version(value)
    except ValueError as exc:
        raise ReleaseSecurityError(f"Tor Browser version state at {path} is malformed.") from exc


def advance_high_water(path: Path, version: Version) -> None:
    """Atomically persist a successful version without lowering the existing floor."""
    current = read_optional_version(path)
    if current is not None and current >= version:
        return

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}-",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w") as temporary:
            temporary.write(f"{version}\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
        directory = os.open(path.parent, os.O_DIRECTORY | os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary_path.unlink(missing_ok=True)
