import fcntl
import os
import shutil
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO

LOCK_FILENAME = "lifecycle.lock"
EPHEMERAL_RUNTIME_ROOT = Path("/run/user/1000/securedrop-tor-browser")
RUNTIME_ROOT = EPHEMERAL_RUNTIME_ROOT
ABANDONED_PATTERNS = (".install-*", ".highest-version-*")


class LifecycleBusy(Exception):
    """Another Tor Browser lifecycle currently owns the operating-system lock."""


def _unsafe_path_error(path: Path, detail: str) -> OSError:
    return OSError(f"Tor Browser path {path} is unsafe: {detail}.")


def _validate_path_components(path: Path) -> None:
    for component in (path, *path.parents):
        metadata = os.lstat(component)
        if not stat.S_ISDIR(metadata.st_mode):
            raise _unsafe_path_error(component, "every path component must be a real directory")
        mode = stat.S_IMODE(metadata.st_mode)
        trusted_owner = component == Path("/") or metadata.st_uid in {0, os.getuid()}
        sticky_temporary_directory = component == Path("/tmp") and bool(mode & stat.S_ISVTX)
        if (not trusted_owner and not sticky_temporary_directory) or (
            mode & 0o022 and not sticky_temporary_directory
        ):
            raise _unsafe_path_error(
                component, "a parent directory has unsafe ownership or permissions"
            )


def ensure_private_directory(path: Path) -> None:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        path.mkdir(mode=0o700, parents=True)
        path.chmod(0o700)
        metadata = os.lstat(path)
    _validate_path_components(path)
    if not stat.S_ISDIR(metadata.st_mode):
        raise _unsafe_path_error(path, "it must be a real directory")
    if metadata.st_uid != os.getuid():
        raise _unsafe_path_error(path, "it has the wrong owner")
    if stat.S_IMODE(metadata.st_mode) != 0o700:
        raise _unsafe_path_error(path, "permissions must be 0700")


def _validate_optional_directory(path: Path) -> bool:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    if not stat.S_ISDIR(metadata.st_mode):
        raise _unsafe_path_error(path, "it must be a real directory")
    if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o022:
        raise _unsafe_path_error(path, "ownership or permissions allow unsafe changes")
    return True


def _validate_optional_file(path: Path) -> bool:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(metadata.st_mode):
        raise _unsafe_path_error(path, "it must be a regular file")
    if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o600:
        raise _unsafe_path_error(path, "ownership or permissions must be private")
    return True


def _open_lock(path: Path) -> IO[bytes]:
    descriptor = os.open(
        path,
        os.O_CLOEXEC | os.O_CREAT | os.O_NOFOLLOW | os.O_RDWR,
        0o600,
    )
    metadata = os.fstat(descriptor)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o600
    ):
        os.close(descriptor)
        raise _unsafe_path_error(path, "the lifecycle lock must be a user-owned 0600 file")
    return os.fdopen(descriptor, "r+b")


def _remove_path(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        path.unlink(missing_ok=True)
    else:
        shutil.rmtree(path)


def _recover_durable_state(state_root: Path) -> None:
    browser = state_root / "browser"
    browser_exists = _validate_optional_directory(browser)
    if browser_exists:
        _validate_optional_file(browser / ".securedrop-version")
    _validate_optional_file(state_root / "highest-version")

    retired = sorted(state_root.glob(".retired-*"))
    if len(retired) > 1:
        raise OSError("Tor Browser replacement is ambiguous: multiple retired browsers exist.")
    if retired:
        _validate_optional_directory(retired[0])
        if browser_exists:
            shutil.rmtree(retired[0])
        else:
            os.replace(retired[0], browser)

    for pattern in ABANDONED_PATTERNS:
        for path in state_root.glob(pattern):
            _remove_path(path)


def cleanup_runtime(runtime_root: Path) -> None:
    for path in runtime_root.iterdir():
        if path.name != LOCK_FILENAME:
            _remove_path(path)


@contextmanager
def exclusive_lifecycle(
    state_root: Path,
    runtime_root: Path | None = None,
) -> Iterator[None]:
    """Validate state, recover replacement, and own the ephemeral lifecycle lock."""
    if runtime_root is None:
        runtime_root = RUNTIME_ROOT
    ensure_private_directory(state_root)
    ensure_private_directory(runtime_root)
    with _open_lock(runtime_root / LOCK_FILENAME) as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise LifecycleBusy from exc
        cleanup_runtime(runtime_root)
        _recover_durable_state(state_root)
        yield
