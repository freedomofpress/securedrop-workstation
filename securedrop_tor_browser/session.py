import os
import shutil
import subprocess
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Protocol

from securedrop_tor_browser import lifecycle

TOR_PROFILE_NAME = "securedrop-tor-browser-tor"
FIREFOX_PROFILE_NAME = "securedrop-tor-browser-firefox"
AA_EXEC_PATH = Path("/usr/bin/aa-exec")
RUNTIME_ROOT = lifecycle.RUNTIME_ROOT
SOCKS_SOCKET_NAME = "socks.socket"
CONTROL_SOCKET_NAME = "control.socket"
CONTROL_COOKIE_NAME = "control.authcookie"
SOCKET_START_TIMEOUT_SECONDS = 15.0
PROCESS_STOP_TIMEOUT_SECONDS = 5.0
POLL_INTERVAL_SECONDS = 0.1


class SessionError(Exception):
    """A managed browser session could not be started or supervised safely."""


class Process(Protocol):
    def poll(self) -> int | None: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...

    def wait(self, timeout: float | None = None) -> int: ...


Popen = Callable[..., Process]


def browser_environment(
    runtime: Path,
    *,
    inherited: Mapping[str, str] = os.environ,
) -> dict[str, str]:
    """Build the small, explicit environment inherited by confined Firefox."""
    home = runtime / "home"
    environment = {
        "PATH": os.defpath,
        "HOME": str(home),
        "XDG_CACHE_HOME": str(runtime / "cache"),
        "XDG_CONFIG_HOME": str(runtime / "config"),
        "XDG_DATA_HOME": str(runtime / "data"),
        "TMPDIR": str(runtime / "tmp"),
        "GSETTINGS_BACKEND": "memory",
        "__GL_SHADER_DISK_CACHE": "0",
        "TOR_SKIP_LAUNCH": "1",
        "TOR_SOCKS_IPC_PATH": str(runtime / SOCKS_SOCKET_NAME),
        "TOR_CONTROL_IPC_PATH": str(runtime / CONTROL_SOCKET_NAME),
        "TOR_CONTROL_COOKIE_AUTH_FILE": str(runtime / CONTROL_COOKIE_NAME),
    }
    for name in (
        "DBUS_SESSION_BUS_ADDRESS",
        "DISPLAY",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "WAYLAND_DISPLAY",
    ):
        if name in inherited:
            environment[name] = inherited[name]
    return environment


def _copy_xauthority(runtime: Path, environment: dict[str, str]) -> None:
    source_name = os.environ.get("XAUTHORITY")
    if not source_name:
        return
    source = Path(source_name)
    destination = runtime / "xauthority"
    try:
        shutil.copyfile(source, destination)
    except OSError as exc:
        raise SessionError("The graphical session credential could not be isolated.") from exc
    destination.chmod(0o600)
    environment["XAUTHORITY"] = str(destination)


def _require_bundle_layout(state_root: Path) -> tuple[Path, Path, Path, Path]:
    browser = state_root / "browser" / "Browser"
    tor = browser / "TorBrowser" / "Tor" / "tor"
    firefox = browser / "firefox.real"
    baseline = browser / "TorBrowser" / "Data" / "Browser" / "profile.default"
    if (
        not tor.is_file()
        or not os.access(tor, os.X_OK)
        or not firefox.is_file()
        or not os.access(firefox, os.X_OK)
        or not baseline.is_dir()
    ):
        raise SessionError("The managed Tor Browser installation is incomplete.")
    return browser, tor, firefox, baseline


def _wait_for_tor(
    process: Process,
    runtime: Path,
    *,
    monotonic: Callable[[], float],
    sleep: Callable[[float], None],
) -> None:
    deadline = monotonic() + SOCKET_START_TIMEOUT_SECONDS
    managed_endpoints = (
        runtime / SOCKS_SOCKET_NAME,
        runtime / CONTROL_SOCKET_NAME,
        runtime / CONTROL_COOKIE_NAME,
    )
    while not all(path.exists() for path in managed_endpoints):
        if process.poll() is not None:
            raise SessionError("Bundled Tor exited before its managed sockets were ready.")
        if monotonic() >= deadline:
            raise SessionError("Bundled Tor did not make its managed sockets ready in time.")
        sleep(POLL_INTERVAL_SECONDS)


def _stop_process(process: Process | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=PROCESS_STOP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=PROCESS_STOP_TIMEOUT_SECONDS)


def _cleanup_session(
    browser_process: Process | None,
    tor_process: Process | None,
    runtime: Path,
) -> None:
    """Attempt every teardown step and report if the session was not fully cleaned."""
    cleanup_error: OSError | subprocess.SubprocessError | None = None
    for process in (browser_process, tor_process):
        try:
            _stop_process(process)
        except (OSError, subprocess.SubprocessError) as exc:
            if cleanup_error is None:
                cleanup_error = exc

    try:
        lifecycle.cleanup_runtime(runtime)
    except FileNotFoundError:
        pass
    except OSError as exc:
        if cleanup_error is None:
            cleanup_error = exc

    if cleanup_error is not None:
        raise SessionError(
            "The managed Tor Browser session cleanup did not complete."
        ) from cleanup_error


def _supervise(
    tor_process: Process,
    browser_process: Process,
    *,
    sleep: Callable[[float], None],
) -> int:
    while True:
        tor_status = tor_process.poll()
        browser_status = browser_process.poll()
        if tor_status is not None:
            _stop_process(browser_process)
            raise SessionError("Bundled Tor exited while Tor Browser was running.")
        if browser_status is not None:
            if browser_status != 0:
                raise SessionError("Tor Browser exited unexpectedly.")
            return browser_status
        sleep(POLL_INTERVAL_SECONDS)


def run_browser_session(
    config: Mapping[str, Any],
    state_root: Path,
    *,
    popen: Popen = subprocess.Popen,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    runtime_root: Path | None = None,
) -> int:
    """Run one fresh-profile Tor and Firefox session under enforced confinement."""
    browser, tor, firefox, baseline = _require_bundle_layout(state_root)
    torrc_value = config.get("torrc_path")
    if not isinstance(torrc_value, str) or not torrc_value:
        raise SessionError("The managed Tor configuration path is invalid.")

    runtime = RUNTIME_ROOT if runtime_root is None else runtime_root
    tor_process: Process | None = None
    browser_process: Process | None = None
    try:
        lifecycle.ensure_private_directory(runtime)
        (runtime / "tor").mkdir(mode=0o700)
        for directory in ("cache", "config", "data", "home", "tmp"):
            (runtime / directory).mkdir(mode=0o700)
        profile = runtime / "profile"
        shutil.copytree(baseline, profile, symlinks=True)

        environment = browser_environment(runtime)
        _copy_xauthority(runtime, environment)
        tor_environment = {
            "HOME": environment["HOME"],
            "LD_LIBRARY_PATH": str(browser / "TorBrowser" / "Tor"),
            "PATH": os.defpath,
            "TMPDIR": environment["TMPDIR"],
        }
        tor_process = popen(
            [
                str(AA_EXEC_PATH),
                f"--profile={TOR_PROFILE_NAME}",
                "--",
                str(tor),
                "-f",
                torrc_value,
            ],
            cwd=browser,
            env=tor_environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _wait_for_tor(tor_process, runtime, monotonic=monotonic, sleep=sleep)

        browser_process = popen(
            [
                str(AA_EXEC_PATH),
                f"--profile={FIREFOX_PROFILE_NAME}",
                "--",
                str(firefox),
                "--no-remote",
                "--profile",
                str(profile),
            ],
            cwd=browser,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return _supervise(tor_process, browser_process, sleep=sleep)
    finally:
        _cleanup_session(browser_process, tor_process, runtime)
