"""Verified, atomic Tor Browser bundle installation."""

from __future__ import annotations

import http.client
import json
import os
import re
import shutil
import ssl
import subprocess
import tarfile
import tempfile
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from types import TracebackType
from typing import IO, Any, Protocol, Self
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urljoin, urlsplit

from securedrop_tor_browser.release import (
    DOWNLOAD_HOSTS,
    MAX_REDIRECTS,
    REQUEST_TIMEOUT_SECONDS,
    STATE_ROOT,
    StableRelease,
    advance_high_water,
)

Download = Callable[[str, Path, Callable[[], bool]], None]
Verify = Callable[[Path, Path, Path, str], None]
Run = Callable[..., subprocess.CompletedProcess[str]]
DOWNLOAD_CHUNK_BYTES = 256 * 1024


class DownloadResponse(Protocol):
    @property
    def status(self) -> int | None: ...

    @property
    def headers(self) -> Any: ...

    def read(self, size: int = -1) -> bytes: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...


OpenUrl = Callable[[urllib_request.Request, float], DownloadResponse]


def _ignore_message(_message: str) -> None:
    pass


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
        """Return redirects to the allowlist policy instead of following them."""


def _open_url(request: urllib_request.Request, timeout: float) -> DownloadResponse:
    opener = urllib_request.build_opener(_NoRedirectHandler())
    try:
        return opener.open(request, timeout=timeout)
    except urllib_error.HTTPError as exc:
        return exc


class InstallationError(Exception):
    """Base class for a Tor Browser installation failure."""


class InstallationSecurityError(InstallationError):
    """A downloaded artifact failed an authenticity or integrity check."""


class InstallationCancelled(InstallationError):
    """The user cancelled while a bundle download was still interruptible."""


def _check_cancelled(cancelled: Callable[[], bool]) -> None:
    if cancelled():
        raise InstallationCancelled("Tor Browser bundle download was cancelled.")


def _validate_download_url(url: str) -> None:
    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise InstallationSecurityError("The bundle URL has an invalid port.") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname not in DOWNLOAD_HOSTS
        or port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise InstallationSecurityError("The bundle URL is not an approved Tor HTTPS location.")


def _is_tls_failure(exc: BaseException) -> bool:
    if isinstance(exc, ssl.SSLError):
        return True
    return isinstance(exc, urllib_error.URLError) and isinstance(exc.reason, ssl.SSLError)


def download_file(
    url: str,
    destination: Path,
    cancelled: Callable[[], bool],
    *,
    open_url: OpenUrl = _open_url,
) -> None:
    """Stream one artifact from an allowlisted Tor HTTPS host into staging."""
    try:
        for redirect_count in range(MAX_REDIRECTS + 1):
            _check_cancelled(cancelled)
            _validate_download_url(url)
            request = urllib_request.Request(  # noqa: S310 - URL is restricted above.
                url,
                headers={"User-Agent": "SecureDrop-Workstation-Tor-Browser-Updater"},
            )
            try:
                response = open_url(request, REQUEST_TIMEOUT_SECONDS)
            except (urllib_error.URLError, TimeoutError, OSError) as exc:
                if _is_tls_failure(exc):
                    raise InstallationSecurityError(
                        "The Tor Browser bundle failed HTTPS validation."
                    ) from exc
                raise InstallationError("The Tor Browser bundle could not be downloaded.") from exc

            with response:
                headers = {name.lower(): value.strip() for name, value in response.headers.items()}
                if response.status in {301, 302, 303, 307, 308}:
                    if redirect_count == MAX_REDIRECTS:
                        raise InstallationSecurityError(
                            "The Tor Browser bundle redirected too many times."
                        )
                    location = headers.get("location")
                    if not location:
                        raise InstallationSecurityError(
                            "The Tor Browser bundle redirect is malformed."
                        )
                    url = urljoin(url, location)
                    _validate_download_url(url)
                    continue
                if response.status != 200:
                    raise InstallationError(
                        f"The Tor Browser bundle download returned HTTP {response.status}."
                    )

                with destination.open("xb") as stream:
                    while True:
                        _check_cancelled(cancelled)
                        chunk = response.read(DOWNLOAD_CHUNK_BYTES)
                        _check_cancelled(cancelled)
                        if not chunk:
                            return
                        stream.write(chunk)
        raise AssertionError("unreachable")
    except BaseException:
        with suppress(FileNotFoundError):
            destination.unlink()
        raise


def verify_bundle_signature(
    bundle_path: Path,
    signature_path: Path,
    signing_key_path: Path,
    signing_key_fingerprint: str,
    *,
    run: Run = subprocess.run,
) -> None:
    """Verify a detached signature using only the Workstation-pinned OpenPGP key."""
    expected = signing_key_fingerprint.upper()
    if re.fullmatch(r"[0-9A-F]{40}", expected) is None:
        raise InstallationSecurityError("The pinned Tor Browser signing key is invalid.")

    keyring_path = bundle_path.parent / "pinned-key.gpg"
    try:
        dearmor = run(
            [
                "gpg",
                "--batch",
                "--no-options",
                "--dearmor",
                "--output",
                str(keyring_path),
                str(signing_key_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if dearmor.returncode != 0:
            raise InstallationSecurityError("The pinned Tor Browser signing key cannot be used.")

        verified = run(
            [
                "gpgv",
                "--status-fd",
                "1",
                "--keyring",
                str(keyring_path),
                str(signature_path),
                str(bundle_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        status = verified.stdout
        if "[GNUPG:] NO_PUBKEY " in status:
            raise InstallationSecurityError(
                "The Tor Browser bundle was signed by an unknown signing key."
            )
        valid_signers = []
        for line in status.splitlines():
            fields = line.split()
            if len(fields) >= 3 and fields[:2] == ["[GNUPG:]", "VALIDSIG"]:
                valid_signers.append({fields[2].upper(), fields[-1].upper()})
        if verified.returncode != 0 or not any(expected in signers for signers in valid_signers):
            raise InstallationSecurityError("The Tor Browser bundle has an invalid signature.")
    except OSError as exc:
        raise InstallationError("Tor Browser signature verification could not be run.") from exc
    finally:
        with suppress(FileNotFoundError):
            keyring_path.unlink()


def _validate_extracted_version(browser: Path, stable: StableRelease) -> None:
    version_path = browser / "Browser" / "tbb_version.json"
    try:
        document = json.loads(version_path.read_text())
        bundled_version = document["version"]
    except (OSError, KeyError, json.JSONDecodeError, TypeError) as exc:
        raise InstallationSecurityError(
            "The verified Tor Browser bundle has malformed version information."
        ) from exc
    if not isinstance(bundled_version, str) or bundled_version != str(stable.version):
        raise InstallationSecurityError(
            "The verified Tor Browser bundle version does not match the advertised release."
        )


def install_verified_bundle(
    stable: StableRelease,
    *,
    signing_key_path: Path,
    signing_key_fingerprint: str,
    state_root: Path = STATE_ROOT,
    download: Download = download_file,
    verify: Verify = verify_bundle_signature,
    cancelled: Callable[[], bool] = lambda: False,
    disable_cancellation: Callable[[str], None] = _ignore_message,
) -> None:
    """Stage, verify, extract, and atomically activate one advertised release."""
    state_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    installations = state_root / "installations"
    installations.mkdir(mode=0o700, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".install-", dir=state_root))
    installed_path: Path | None = None
    pending_active: Path | None = None
    activated = False

    try:
        bundle_path = staging / "bundle.tar.xz"
        signature_path = staging / "bundle.tar.xz.asc"
        download(stable.bundle_url, bundle_path, cancelled)
        download(stable.signature_url, signature_path, cancelled)
        disable_cancellation("Verifying and installing Tor Browser…")
        verify(bundle_path, signature_path, signing_key_path, signing_key_fingerprint)

        extracted = staging / "extracted"
        try:
            with tarfile.open(bundle_path, mode="r:xz") as archive:
                archive.extractall(extracted, filter="data")
        except (OSError, tarfile.TarError) as exc:
            raise InstallationError(
                "The verified Tor Browser bundle could not be extracted."
            ) from exc

        browser = extracted / "tor-browser"
        _validate_extracted_version(browser, stable)
        installation_name = f"{stable.version}-{staging.name.removeprefix('.install-')}"
        installed_path = installations / installation_name
        try:
            (browser / ".securedrop-version").write_text(f"{stable.version}\n")
            os.replace(browser, installed_path)
        except OSError as exc:
            raise InstallationError(
                "The verified Tor Browser bundle could not be installed."
            ) from exc

        pending_active = state_root / f".active-{staging.name.removeprefix('.install-')}"
        pending_active.symlink_to(installed_path)
        try:
            os.replace(pending_active, state_root / "active")
        except OSError as exc:
            raise InstallationError(
                "The verified Tor Browser bundle could not be atomically activated."
            ) from exc
        activated = True
        advance_high_water(state_root / "highest-version", stable.version)
    finally:
        if pending_active is not None:
            with suppress(FileNotFoundError):
                pending_active.unlink()
        shutil.rmtree(staging, ignore_errors=True)
        if installed_path is not None and not activated:
            shutil.rmtree(installed_path, ignore_errors=True)
