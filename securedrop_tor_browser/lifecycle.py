import fcntl
import os
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO

LOCK_FILENAME = "lifecycle.lock"
RUNTIME_DIRECTORY = "runtime"
ABANDONED_PATTERNS = (".install-*", ".active-*", ".highest-version-*")


class LifecycleBusy(Exception):
    """Another Tor Browser lifecycle currently owns the operating-system lock."""


def _open_lock(path: Path) -> IO[bytes]:
    descriptor = os.open(
        path,
        os.O_CLOEXEC | os.O_CREAT | os.O_NOFOLLOW | os.O_RDWR,
        0o600,
    )
    return os.fdopen(descriptor, "r+b")


def _remove_path(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        path.unlink(missing_ok=True)
    else:
        shutil.rmtree(path)


def _cleanup_abandoned_state(state_root: Path) -> None:
    for pattern in ABANDONED_PATTERNS:
        for path in state_root.glob(pattern):
            _remove_path(path)
    _remove_path(state_root / RUNTIME_DIRECTORY)


@contextmanager
def exclusive_lifecycle(state_root: Path) -> Iterator[None]:
    """Own the single kernel lock for checking, updating, running, and cleanup."""
    state_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    with _open_lock(state_root / LOCK_FILENAME) as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise LifecycleBusy from exc
        _cleanup_abandoned_state(state_root)
        yield
