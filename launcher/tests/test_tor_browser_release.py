from __future__ import annotations

import json
from collections.abc import Callable
from contextlib import nullcontext
from pathlib import Path
from types import TracebackType
from typing import Self
from unittest import mock
from urllib import request as urllib_request

import pytest

from securedrop_tor_browser import main as launcher
from securedrop_tor_browser import release


class ScriptedTransport:
    def __init__(self, *steps: release.HttpResponse | Exception) -> None:
        self.steps = list(steps)
        self.urls: list[str] = []
        self.timeouts: list[float] = []

    def __call__(
        self, url: str, timeout: float, cancelled: Callable[[], bool]
    ) -> release.HttpResponse:
        self.urls.append(url)
        self.timeouts.append(timeout)
        if cancelled():
            raise release.ReleaseCancelled("cancelled during transport")
        step = self.steps.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


class StreamingResponse:
    def __init__(self, *chunks: bytes, status: int = 200, **headers: str) -> None:
        self.chunks = list(chunks)
        self.status = status
        self.headers = headers
        self.read_calls = 0
        self.closed = False

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def read(self, size: int = -1) -> bytes:
        self.read_calls += 1
        if not self.chunks:
            return b""
        return self.chunks.pop(0)

    def close(self) -> None:
        self.closed = True


def metadata(version: str = "15.0.19") -> bytes:
    return json.dumps(
        {
            "binary": (
                f"https://dist.torproject.org/torbrowser/{version}/"
                f"tor-browser-linux-x86_64-{version}.tar.xz"
            ),
            "git_tag": f"tbb-{version}-build1",
            "sig": (
                f"https://dist.torproject.org/torbrowser/{version}/"
                f"tor-browser-linux-x86_64-{version}.tar.xz.asc"
            ),
            "version": version,
        }
    ).encode()


def response(body: bytes = b"", status: int = 200, **headers: str) -> release.HttpResponse:
    return release.HttpResponse(status, headers, body)


def test_discovers_current_linux_release_over_allowlisted_https():
    transport = ScriptedTransport(response(metadata()))

    discovered = release.discover_stable_release(transport=transport)

    assert discovered.version == release.Version("15.0.19")
    assert discovered.bundle_url.startswith("https://dist.torproject.org/")
    assert transport.urls == [release.METADATA_URL]
    assert transport.timeouts == [release.REQUEST_TIMEOUT_SECONDS]


@pytest.mark.parametrize(
    "location",
    [
        "http://aus1.torproject.org/torbrowser/update_3/release/download-linux-x86_64.json",
        "https://example.org/download-linux-x86_64.json",
    ],
)
def test_rejects_unsafe_metadata_redirect_without_following_it(location):
    transport = ScriptedTransport(response(status=302, location=location))

    with pytest.raises(release.ReleaseSecurityError):
        release.discover_stable_release(transport=transport)

    assert transport.urls == [release.METADATA_URL]


def test_accepts_allowlisted_redirect_and_limits_redirect_chains():
    redirected = (
        "https://aus2.torproject.org/torbrowser/update_3/release/" "download-linux-x86_64.json"
    )
    transport = ScriptedTransport(
        response(status=302, location=redirected),
        response(metadata()),
    )
    assert release.discover_stable_release(transport=transport).version == release.Version(
        "15.0.19"
    )

    looping = ScriptedTransport(
        *[
            response(status=302, location=release.METADATA_URL)
            for _ in range(release.MAX_REDIRECTS + 1)
        ]
    )
    with pytest.raises(release.ReleaseSecurityError, match="redirect"):
        release.discover_stable_release(transport=looping)


def test_rejects_oversized_response_and_declared_content_length():
    with pytest.raises(release.ReleaseSecurityError, match="large"):
        release.discover_stable_release(
            transport=ScriptedTransport(response(b"x" * (release.MAX_METADATA_BYTES + 1)))
        )
    with pytest.raises(release.ReleaseSecurityError, match="large"):
        release.discover_stable_release(
            transport=ScriptedTransport(
                response(b"{}", **{"content-length": str(release.MAX_METADATA_BYTES + 1)})
            )
        )


def test_transient_failure_retries_twice_with_bounded_backoff():
    transport = ScriptedTransport(
        release.TransientReleaseError("offline"),
        response(status=503),
        response(metadata()),
    )
    delays: list[float] = []

    discovered = release.discover_stable_release(transport=transport, sleep=delays.append)

    assert discovered.version == release.Version("15.0.19")
    assert delays == [0.25, 0.5]
    assert len(transport.urls) == 3


def test_unavailable_metadata_stops_after_two_automatic_retries():
    transport = ScriptedTransport(response(status=503), response(status=503), response(status=503))

    with pytest.raises(release.TransientReleaseError):
        release.discover_stable_release(transport=transport, sleep=lambda _: None)

    assert len(transport.urls) == 3


@pytest.mark.parametrize(
    "body",
    [
        b"not json",
        b"{}",
        json.dumps(
            {
                "version": "15.0.19",
                "binary": "http://dist.torproject.org/browser.tar.xz",
                "sig": "https://dist.torproject.org/browser.tar.xz.asc",
            }
        ).encode(),
        json.dumps(
            {
                "version": "15.0.19",
                "binary": "https://example.org/browser.tar.xz",
                "sig": "https://dist.torproject.org/browser.tar.xz.asc",
            }
        ).encode(),
    ],
)
def test_malformed_or_untrusted_metadata_is_blocked(body):
    with pytest.raises(release.ReleaseSecurityError):
        release.discover_stable_release(transport=ScriptedTransport(response(body)))


@pytest.mark.parametrize(
    ("advertised", "installed", "high_water", "minimum", "expected"),
    [
        ("15.0.19", "15.0.19", None, "15.0.1", release.ReleaseAction.CURRENT),
        ("15.0.19", None, None, "15.0.1", release.ReleaseAction.INSTALL),
        ("15.0.19", "15.0.18", None, "15.0.1", release.ReleaseAction.INSTALL),
        ("15.0.18", "15.0.19", None, "15.0.1", release.ReleaseAction.BLOCKED),
        ("15.0.18", None, "15.0.19", "15.0.1", release.ReleaseAction.BLOCKED),
        ("15.0.0", None, None, "15.0.1", release.ReleaseAction.BLOCKED),
    ],
)
def test_release_policy_covers_current_install_stale_and_downgrade_metadata(
    advertised, installed, high_water, minimum, expected
):
    decision = release.decide_release_action(
        release.Version(advertised),
        installed=release.Version(installed) if installed else None,
        high_water=release.Version(high_water) if high_water else None,
        minimum=release.Version(minimum),
    )
    assert decision.action is expected


def test_cancellation_prevents_metadata_request():
    transport = ScriptedTransport(response(metadata()))

    with pytest.raises(release.ReleaseCancelled):
        release.discover_stable_release(transport=transport, cancelled=lambda: True)

    assert transport.urls == []


def test_default_transport_uses_direct_https_without_subprocess():
    stream = StreamingResponse(metadata(), b"")
    opener = mock.Mock()
    opener.open.return_value = stream

    with (
        mock.patch.object(urllib_request, "build_opener", return_value=opener),
        mock.patch(
            "subprocess.Popen",
            side_effect=AssertionError("release discovery must not invoke subprocess"),
        ) as popen,
    ):
        discovered = release.discover_stable_release()

    assert discovered.version == release.Version("15.0.19")
    popen.assert_not_called()
    request = opener.open.call_args.args[0]
    assert request.full_url == release.METADATA_URL
    assert opener.open.call_args.kwargs == {"timeout": release.REQUEST_TIMEOUT_SECONDS}


def test_launcher_recognizes_matching_installed_release_as_current():
    config = {"minimum_version": "15.0.1"}
    discovered = release.StableRelease(
        release.Version("15.0.19"),
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz",
        "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz.asc",
    )
    with (
        pytest.MonkeyPatch.context() as monkeypatch,
    ):
        monkeypatch.setattr(launcher.core, "load_managed_config", lambda: config)
        monkeypatch.setattr(
            launcher.frontend,
            "metadata_retrieval",
            lambda: nullcontext(lambda: False),
        )
        monkeypatch.setattr(
            launcher.release, "discover_stable_release", lambda **kwargs: discovered
        )
        monkeypatch.setattr(
            launcher.release,
            "read_optional_version",
            lambda path: release.Version("15.0.19")
            if path == release.INSTALLED_VERSION_PATH
            else None,
        )
        ready: list[str] = []
        monkeypatch.setattr(
            launcher.frontend, "show_ready", lambda version: ready.append(version) or 0
        )

        assert launcher.main() == 0

    assert ready == ["15.0.19"]


def test_launcher_offers_retry_and_close_after_transient_retries_are_exhausted(
    monkeypatch,
):
    config = {
        "minimum_version": "15.0.1",
        "signing_key_path": "/managed/pinned-key.asc",
        "signing_key_fingerprint": "EF6E286DDA85EA2A4BA7DE684E2C6E8793298290",
    }
    outcomes: list[release.StableRelease | Exception] = [
        release.TransientReleaseError("offline"),
        release.StableRelease(
            release.Version("15.0.19"),
            "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz",
            "https://dist.torproject.org/torbrowser/15.0.19/browser.tar.xz.asc",
        ),
    ]

    def discover(**kwargs):
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(launcher.core, "load_managed_config", lambda: config)
    monkeypatch.setattr(launcher.frontend, "metadata_retrieval", lambda: nullcontext(lambda: False))
    monkeypatch.setattr(launcher.release, "discover_stable_release", discover)
    monkeypatch.setattr(launcher.release, "read_optional_version", lambda path: None)
    monkeypatch.setattr(launcher.frontend, "show_retry_or_close", lambda *args: True)
    progress = mock.Mock()
    monkeypatch.setattr(
        launcher.frontend, "bundle_installation", lambda _version: nullcontext(progress)
    )
    install_bundle = mock.Mock()
    monkeypatch.setattr(launcher.install, "install_verified_bundle", install_bundle)
    ready = mock.Mock(return_value=0)
    monkeypatch.setattr(launcher.frontend, "show_ready", ready)
    show_error = mock.Mock(return_value=1)
    monkeypatch.setattr(launcher.frontend, "show_error", show_error)

    assert launcher.main() == 0
    assert not outcomes
    install_bundle.assert_called_once()
    ready.assert_called_once_with("15.0.19")
    show_error.assert_not_called()


@pytest.mark.parametrize(
    "failure",
    [
        release.ReleaseSecurityError("malformed"),
        release.ReleaseCancelled("cancelled"),
    ],
)
def test_launcher_security_failure_or_cancellation_has_no_retry_or_launch(monkeypatch, failure):
    monkeypatch.setattr(launcher.core, "load_managed_config", lambda: {"minimum_version": "15.0.1"})

    def fail(**kwargs):
        raise failure

    monkeypatch.setattr(launcher.frontend, "metadata_retrieval", lambda: nullcontext(lambda: False))
    monkeypatch.setattr(launcher.release, "discover_stable_release", fail)
    retry = mock.Mock()
    ready = mock.Mock()
    monkeypatch.setattr(launcher.frontend, "show_retry_or_close", retry)
    monkeypatch.setattr(launcher.frontend, "show_ready", ready)
    monkeypatch.setattr(launcher.frontend, "show_error", lambda *args: 1)

    assert launcher.main() == 1
    retry.assert_not_called()
    ready.assert_not_called()


@pytest.mark.parametrize(
    ("advertised", "installed", "high_water", "minimum"),
    [
        ("15.0.18", "15.0.19", None, "15.0.1"),
        ("15.0.18", None, "15.0.19", "15.0.1"),
        ("15.0.0", None, None, "15.0.1"),
    ],
)
def test_launcher_blocks_stale_downgraded_and_below_minimum_metadata(
    monkeypatch, advertised, installed, high_water, minimum
):
    discovered = release.StableRelease(
        release.Version(advertised),
        f"https://dist.torproject.org/torbrowser/{advertised}/browser.tar.xz",
        f"https://dist.torproject.org/torbrowser/{advertised}/browser.tar.xz.asc",
    )
    versions = iter(
        [
            release.Version(installed) if installed else None,
            release.Version(high_water) if high_water else None,
        ]
    )
    monkeypatch.setattr(launcher.core, "load_managed_config", lambda: {"minimum_version": minimum})
    monkeypatch.setattr(launcher.frontend, "metadata_retrieval", lambda: nullcontext(lambda: False))
    monkeypatch.setattr(launcher.release, "discover_stable_release", lambda **kwargs: discovered)
    monkeypatch.setattr(launcher.release, "read_optional_version", lambda path: next(versions))
    ready = mock.Mock()
    error = mock.Mock(return_value=1)
    monkeypatch.setattr(launcher.frontend, "show_ready", ready)
    monkeypatch.setattr(launcher.frontend, "show_error", error)

    assert launcher.main() == 1
    assert error.call_args.args[0] == "Tor Browser release blocked"
    ready.assert_not_called()


def test_high_water_version_never_decreases(tmp_path: Path) -> None:
    high_water = tmp_path / "highest-version"

    release.advance_high_water(high_water, release.Version("15.0.19"))
    release.advance_high_water(high_water, release.Version("15.0.18"))

    assert high_water.read_text() == "15.0.19\n"


def test_launcher_cancels_direct_streaming_retrieval_without_changing_version_state(
    monkeypatch, tmp_path
):
    installed = tmp_path / "installed"
    high_water = tmp_path / "high-water"
    installed.write_text("15.0.18\n")
    high_water.write_text("15.0.18\n")
    before = (installed.read_bytes(), high_water.read_bytes())
    stream = StreamingResponse(b"{", metadata()[1:], b"")
    opener = mock.Mock()
    opener.open.return_value = stream

    monkeypatch.setattr(
        launcher.core,
        "load_managed_config",
        lambda: {"minimum_version": "15.0.1"},
    )
    monkeypatch.setattr(launcher.release, "INSTALLED_VERSION_PATH", installed)
    monkeypatch.setattr(launcher.release, "HIGH_WATER_VERSION_PATH", high_water)
    monkeypatch.setattr(
        launcher.frontend,
        "metadata_retrieval",
        lambda: nullcontext(lambda: stream.read_calls == 1),
    )
    monkeypatch.setattr(urllib_request, "build_opener", lambda *handlers: opener)
    popen = mock.Mock(side_effect=AssertionError("release discovery must not invoke subprocess"))
    monkeypatch.setattr("subprocess.Popen", popen)
    ready = mock.Mock()
    monkeypatch.setattr(launcher.frontend, "show_ready", ready)
    monkeypatch.setattr(launcher.frontend, "show_error", lambda *args: 1)

    assert launcher.main() == 1
    assert (installed.read_bytes(), high_water.read_bytes()) == before
    assert stream.closed
    assert stream.read_calls == 1
    popen.assert_not_called()
    ready.assert_not_called()
