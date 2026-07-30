from pathlib import Path

import pytest

from securedrop_tor_browser import lifecycle


def test_second_lifecycle_is_rejected_while_first_owns_kernel_lock(tmp_path: Path) -> None:
    state_root = tmp_path / "state"

    with (
        lifecycle.exclusive_lifecycle(state_root),
        pytest.raises(lifecycle.LifecycleBusy),
        lifecycle.exclusive_lifecycle(state_root),
    ):
        pytest.fail("a second lifecycle must not start")


def test_persistent_unlocked_lockfile_does_not_block_later_lifecycle(tmp_path: Path) -> None:
    state_root = tmp_path / "state"

    with lifecycle.exclusive_lifecycle(state_root):
        pass

    assert (state_root / lifecycle.LOCK_FILENAME).is_file()
    with lifecycle.exclusive_lifecycle(state_root):
        pass


def test_lifecycle_cleans_abandoned_state_without_damaging_installations(
    tmp_path: Path,
) -> None:
    state_root = tmp_path / "state"
    retained = state_root / "installations" / "15.0.19-retained"
    retained.mkdir(parents=True)
    active = state_root / "active"
    active.symlink_to(retained)
    (state_root / ".install-abandoned").mkdir()
    (state_root / ".active-abandoned").symlink_to(retained)
    (state_root / ".highest-version-abandoned").write_text("partial")
    runtime_profile = state_root / lifecycle.RUNTIME_DIRECTORY / "profile-abandoned"
    runtime_profile.mkdir(parents=True)
    (runtime_profile / "cookies.sqlite").write_text("session state")

    with lifecycle.exclusive_lifecycle(state_root):
        assert not (state_root / ".install-abandoned").exists()
        assert not (state_root / ".active-abandoned").exists()
        assert not (state_root / ".highest-version-abandoned").exists()
        assert not (state_root / lifecycle.RUNTIME_DIRECTORY).exists()
        assert active.resolve() == retained
        assert retained.is_dir()
