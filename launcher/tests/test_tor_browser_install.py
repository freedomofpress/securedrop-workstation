from __future__ import annotations

import io
import json
import subprocess
import tarfile
from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import Self
from unittest import mock

import pytest

from securedrop_tor_browser import install, release


def bundle(version: str) -> bytes:
    contents = json.dumps(
        {
            "version": version,
            "architecture": "Linux_x86_64-gcc3",
            "channel": "release",
        }
    ).encode()
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w:xz") as tar:
        info = tarfile.TarInfo("tor-browser/Browser/tbb_version.json")
        info.size = len(contents)
        tar.addfile(info, io.BytesIO(contents))
    return archive.getvalue()


class StreamingDownloadResponse:
    def __init__(self, *chunks: bytes) -> None:
        self.status = 200
        self.headers: dict[str, str] = {}
        self.chunks = list(chunks)
        self.closed = False

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.closed = True

    def read(self, _size: int = -1) -> bytes:
        if not self.chunks:
            return b""
        return self.chunks.pop(0)


def test_first_installation_activates_only_the_verified_advertised_bundle(
    tmp_path: Path,
) -> None:
    stable = release.StableRelease(
        release.Version("15.0.19"),
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz",
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz.asc",
    )
    downloads = {
        stable.bundle_url: bundle("15.0.19"),
        stable.signature_url: b"signature",
    }

    def download(url: str, destination: Path, cancelled: Callable[[], bool]) -> None:
        assert not cancelled()
        destination.write_bytes(downloads[url])

    verifier = mock.Mock()

    install.install_verified_bundle(
        stable,
        signing_key_path=tmp_path / "pinned-key.asc",
        signing_key_fingerprint="EF6E286DDA85EA2A4BA7DE684E2C6E8793298290",
        state_root=tmp_path / "state",
        download=download,
        verify=verifier,
        cancelled=mock.Mock(return_value=False),
    )

    active = tmp_path / "state" / "active"
    assert active.is_symlink()
    assert json.loads((active / "Browser/tbb_version.json").read_text())["version"] == "15.0.19"
    assert release.read_optional_version(active / ".securedrop-version") == release.Version(
        "15.0.19"
    )
    verifier.assert_called_once()
    assert not list((tmp_path / "state").glob(".install-*"))


def test_upgrade_atomically_switches_active_and_retains_previous_installation(
    tmp_path: Path,
) -> None:
    state_root = tmp_path / "state"
    verifier = mock.Mock()

    for version in ("15.0.18", "15.0.19"):
        stable = release.StableRelease(
            release.Version(version),
            f"https://dist.torproject.org/torbrowser/{version}/browser.tar.xz",
            f"https://dist.torproject.org/torbrowser/{version}/browser.tar.xz.asc",
        )
        downloads = {
            stable.bundle_url: bundle(version),
            stable.signature_url: b"signature",
        }

        def download(
            url: str,
            destination: Path,
            cancelled: Callable[[], bool],
        ) -> None:
            assert not cancelled()
            destination.write_bytes(downloads[url])

        install.install_verified_bundle(
            stable,
            signing_key_path=tmp_path / "pinned-key.asc",
            signing_key_fingerprint="EF6E286DDA85EA2A4BA7DE684E2C6E8793298290",
            state_root=state_root,
            download=download,
            verify=verifier,
            cancelled=lambda: False,
        )

    active = state_root / "active"
    assert release.read_optional_version(active / ".securedrop-version") == release.Version(
        "15.0.19"
    )
    retained = sorted(
        path.joinpath(".securedrop-version").read_text().strip()
        for path in (state_root / "installations").iterdir()
    )
    assert retained == ["15.0.18", "15.0.19"]


@pytest.mark.parametrize("reason", ["invalid signature", "unknown signing key"])
def test_signature_failure_preserves_active_installation(
    tmp_path: Path,
    reason: str,
) -> None:
    state_root = tmp_path / "state"
    prior = state_root / "installations" / "15.0.18-existing"
    prior.mkdir(parents=True)
    (prior / ".securedrop-version").write_text("15.0.18\n")
    (state_root / "active").symlink_to(prior)
    stable = release.StableRelease(
        release.Version("15.0.19"),
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz",
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz.asc",
    )
    downloads = {
        stable.bundle_url: bundle("15.0.19"),
        stable.signature_url: b"signature",
    }

    def download(
        url: str,
        destination: Path,
        cancelled: Callable[[], bool],
    ) -> None:
        assert not cancelled()
        destination.write_bytes(downloads[url])

    def reject_signature(
        _bundle: Path,
        _signature: Path,
        _key: Path,
        _fingerprint: str,
    ) -> None:
        raise install.InstallationSecurityError(reason)

    with pytest.raises(install.InstallationSecurityError, match=reason):
        install.install_verified_bundle(
            stable,
            signing_key_path=tmp_path / "pinned-key.asc",
            signing_key_fingerprint="EF6E286DDA85EA2A4BA7DE684E2C6E8793298290",
            state_root=state_root,
            download=download,
            verify=reject_signature,
            cancelled=lambda: False,
        )

    assert (state_root / "active").resolve() == prior
    assert release.read_optional_version(state_root / "active" / ".securedrop-version") == (
        release.Version("15.0.18")
    )
    assert list((state_root / "installations").iterdir()) == [prior]
    assert not list(state_root.glob(".install-*"))


def test_verified_bundle_version_must_match_advertised_release(tmp_path: Path) -> None:
    state_root = tmp_path / "state"
    stable = release.StableRelease(
        release.Version("15.0.19"),
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz",
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz.asc",
    )
    downloads = {
        stable.bundle_url: bundle("15.0.18"),
        stable.signature_url: b"signature",
    }

    def download(
        url: str,
        destination: Path,
        cancelled: Callable[[], bool],
    ) -> None:
        assert not cancelled()
        destination.write_bytes(downloads[url])

    with pytest.raises(install.InstallationSecurityError, match="version"):
        install.install_verified_bundle(
            stable,
            signing_key_path=tmp_path / "pinned-key.asc",
            signing_key_fingerprint="EF6E286DDA85EA2A4BA7DE684E2C6E8793298290",
            state_root=state_root,
            download=download,
            verify=mock.Mock(),
            cancelled=lambda: False,
        )

    assert not (state_root / "active").exists()
    assert not list((state_root / "installations").iterdir())
    assert not list(state_root.glob(".install-*"))


def test_interrupted_download_removes_partial_data_without_changing_durable_state(
    tmp_path: Path,
) -> None:
    state_root = tmp_path / "state"
    prior = state_root / "installations" / "15.0.18-existing"
    prior.mkdir(parents=True)
    (prior / ".securedrop-version").write_text("15.0.18\n")
    (state_root / "active").symlink_to(prior)
    high_water = state_root / "highest-version"
    high_water.write_text("15.0.18\n")
    stable = release.StableRelease(
        release.Version("15.0.19"),
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz",
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz.asc",
    )

    def interrupted_download(
        _url: str,
        destination: Path,
        _cancelled: Callable[[], bool],
    ) -> None:
        destination.write_bytes(b"partial bundle")
        raise install.InstallationCancelled("download cancelled")

    with pytest.raises(install.InstallationCancelled, match="cancelled"):
        install.install_verified_bundle(
            stable,
            signing_key_path=tmp_path / "pinned-key.asc",
            signing_key_fingerprint="EF6E286DDA85EA2A4BA7DE684E2C6E8793298290",
            state_root=state_root,
            download=interrupted_download,
            verify=mock.Mock(),
            cancelled=lambda: True,
        )

    assert (state_root / "active").resolve() == prior
    assert high_water.read_text() == "15.0.18\n"
    assert list((state_root / "installations").iterdir()) == [prior]
    assert not list(state_root.glob(".install-*"))


def test_extraction_failure_does_not_launch_or_modify_active_installation(
    tmp_path: Path,
) -> None:
    state_root = tmp_path / "state"
    prior = state_root / "installations" / "15.0.18-existing"
    prior.mkdir(parents=True)
    (prior / ".securedrop-version").write_text("15.0.18\n")
    (state_root / "active").symlink_to(prior)
    stable = release.StableRelease(
        release.Version("15.0.19"),
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz",
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz.asc",
    )
    downloads = {
        stable.bundle_url: b"not an archive",
        stable.signature_url: b"signature",
    }

    def download(
        url: str,
        destination: Path,
        _cancelled: Callable[[], bool],
    ) -> None:
        destination.write_bytes(downloads[url])

    with pytest.raises(install.InstallationError, match="extract"):
        install.install_verified_bundle(
            stable,
            signing_key_path=tmp_path / "pinned-key.asc",
            signing_key_fingerprint="EF6E286DDA85EA2A4BA7DE684E2C6E8793298290",
            state_root=state_root,
            download=download,
            verify=mock.Mock(),
            cancelled=lambda: False,
        )

    assert (state_root / "active").resolve() == prior
    assert list((state_root / "installations").iterdir()) == [prior]


def test_installation_store_failure_preserves_prior_active_installation(
    tmp_path: Path,
) -> None:
    state_root = tmp_path / "state"
    prior = state_root / "installations" / "15.0.18-existing"
    prior.mkdir(parents=True)
    (prior / ".securedrop-version").write_text("15.0.18\n")
    (state_root / "active").symlink_to(prior)
    stable = release.StableRelease(
        release.Version("15.0.19"),
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz",
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz.asc",
    )
    downloads = {
        stable.bundle_url: bundle("15.0.19"),
        stable.signature_url: b"signature",
    }

    def download(
        url: str,
        destination: Path,
        _cancelled: Callable[[], bool],
    ) -> None:
        destination.write_bytes(downloads[url])

    with (
        mock.patch.object(install.os, "replace", side_effect=OSError("installation failed")),
        pytest.raises(install.InstallationError, match="installed"),
    ):
        install.install_verified_bundle(
            stable,
            signing_key_path=tmp_path / "pinned-key.asc",
            signing_key_fingerprint="EF6E286DDA85EA2A4BA7DE684E2C6E8793298290",
            state_root=state_root,
            download=download,
            verify=mock.Mock(),
            cancelled=lambda: False,
        )

    assert (state_root / "active").resolve() == prior
    assert list((state_root / "installations").iterdir()) == [prior]
    assert not list(state_root.glob(".install-*"))


def test_atomic_switch_failure_preserves_prior_active_installation(tmp_path: Path) -> None:
    state_root = tmp_path / "state"
    active = state_root / "active"
    active.mkdir(parents=True)
    (active / ".securedrop-version").write_text("15.0.18\n")
    stable = release.StableRelease(
        release.Version("15.0.19"),
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz",
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz.asc",
    )
    downloads = {
        stable.bundle_url: bundle("15.0.19"),
        stable.signature_url: b"signature",
    }

    def download(
        url: str,
        destination: Path,
        _cancelled: Callable[[], bool],
    ) -> None:
        destination.write_bytes(downloads[url])

    with pytest.raises(install.InstallationError, match="activate"):
        install.install_verified_bundle(
            stable,
            signing_key_path=tmp_path / "pinned-key.asc",
            signing_key_fingerprint="EF6E286DDA85EA2A4BA7DE684E2C6E8793298290",
            state_root=state_root,
            download=download,
            verify=mock.Mock(),
            cancelled=lambda: False,
        )

    assert release.read_optional_version(active / ".securedrop-version") == release.Version(
        "15.0.18"
    )
    assert not any((state_root / "installations").iterdir())
    assert not list(state_root.glob(".active-*"))


def test_signature_verifier_requires_valid_signature_from_pinned_primary_key(
    tmp_path: Path,
) -> None:
    fingerprint = "EF6E286DDA85EA2A4BA7DE684E2C6E8793298290"
    results = iter(
        [
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess(
                [],
                0,
                (
                    "[GNUPG:] VALIDSIG 0123456789ABCDEF0123456789ABCDEF01234567 "
                    "2026-07-30 0 0 4 0 1 10 00 "
                    f"{fingerprint}\n"
                ),
                "",
            ),
        ]
    )

    install.verify_bundle_signature(
        tmp_path / "bundle.tar.xz",
        tmp_path / "bundle.tar.xz.asc",
        tmp_path / "pinned-key.asc",
        fingerprint,
        run=lambda *args, **kwargs: next(results),
    )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("[GNUPG:] NO_PUBKEY DEADBEEFDEADBEEF", "unknown signing key"),
        ("[GNUPG:] BADSIG DEADBEEFDEADBEEF Other Signer", "invalid signature"),
    ],
)
def test_signature_verifier_rejects_unknown_or_invalid_signature(
    tmp_path: Path,
    status: str,
    expected: str,
) -> None:
    results = iter(
        [
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 2, status, ""),
        ]
    )

    with pytest.raises(install.InstallationSecurityError, match=expected):
        install.verify_bundle_signature(
            tmp_path / "bundle.tar.xz",
            tmp_path / "bundle.tar.xz.asc",
            tmp_path / "pinned-key.asc",
            "EF6E286DDA85EA2A4BA7DE684E2C6E8793298290",
            run=lambda *args, **kwargs: next(results),
        )


def test_bundle_download_rejects_unapproved_host_before_network_activity(
    tmp_path: Path,
) -> None:
    open_url = mock.Mock()

    with pytest.raises(install.InstallationSecurityError, match="approved Tor HTTPS"):
        install.download_file(
            "https://example.org/browser.tar.xz",
            tmp_path / "bundle.tar.xz",
            lambda: False,
            open_url=open_url,
        )

    open_url.assert_not_called()


def test_cancelling_streamed_download_removes_partial_file(tmp_path: Path) -> None:
    response = StreamingDownloadResponse(b"first", b"second")
    checks = iter([False, False, False, True])
    destination = tmp_path / "bundle.tar.xz"

    with pytest.raises(install.InstallationCancelled):
        install.download_file(
            "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz",
            destination,
            lambda: next(checks),
            open_url=lambda _request, _timeout: response,
        )

    assert not destination.exists()
    assert response.closed


def test_cancellation_is_disabled_before_verification_and_activation(tmp_path: Path) -> None:
    stable = release.StableRelease(
        release.Version("15.0.19"),
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz",
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz.asc",
    )
    downloads = {
        stable.bundle_url: bundle("15.0.19"),
        stable.signature_url: b"signature",
    }
    events: list[str] = []

    def download(
        url: str,
        destination: Path,
        _cancelled: Callable[[], bool],
    ) -> None:
        events.append(f"download:{url}")
        destination.write_bytes(downloads[url])

    def verify(_bundle: Path, _signature: Path, _key: Path, _fingerprint: str) -> None:
        events.append("verify")

    install.install_verified_bundle(
        stable,
        signing_key_path=tmp_path / "pinned-key.asc",
        signing_key_fingerprint="EF6E286DDA85EA2A4BA7DE684E2C6E8793298290",
        state_root=tmp_path / "state",
        download=download,
        verify=verify,
        cancelled=lambda: False,
        disable_cancellation=lambda message: events.append(f"disable:{message}"),
    )

    assert events[2].startswith("disable:")
    assert events[3] == "verify"
