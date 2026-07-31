import os
from pathlib import Path

import pytest

from securedrop_tor_browser import lifecycle


def private_roots(tmp_path: Path) -> tuple[Path, Path]:
    state_root = tmp_path / "state"
    runtime_root = tmp_path / "runtime"
    return state_root, runtime_root


def test_runtime_root_is_fixed_and_does_not_consult_xdg_environment() -> None:
    assert Path("/run/user/1000/securedrop-tor-browser") == lifecycle.EPHEMERAL_RUNTIME_ROOT


def test_second_lifecycle_is_rejected_while_first_owns_kernel_lock(tmp_path: Path) -> None:
    state_root, runtime_root = private_roots(tmp_path)

    with (
        lifecycle.exclusive_lifecycle(state_root, runtime_root),
        pytest.raises(lifecycle.LifecycleBusy),
        lifecycle.exclusive_lifecycle(state_root, runtime_root),
    ):
        pytest.fail("a second lifecycle must not start")


def test_interrupted_replacement_restores_the_only_retired_browser(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_root, runtime_root = private_roots(tmp_path)
    retired = state_root / ".retired-crashed"
    retired.mkdir(parents=True)
    retired.chmod(0o755)
    state_root.chmod(0o700)
    (retired / ".securedrop-version").write_text("15.0.18\n")
    (retired / ".securedrop-version").chmod(0o600)
    (state_root / ".install-abandoned").mkdir()

    with lifecycle.exclusive_lifecycle(state_root, runtime_root):
        assert (state_root / "browser" / ".securedrop-version").read_text() == "15.0.18\n"
        assert not retired.exists()
        assert not list(state_root.glob(".install-*"))

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "WARNING recovery: interrupted installation state recovered" in captured.err
    assert ".retired-crashed" not in captured.err
    assert ".install-abandoned" not in captured.err
    assert str(state_root) not in captured.err


def test_completed_replacement_discards_retired_browser_and_ephemeral_state(
    tmp_path: Path,
) -> None:
    state_root, runtime_root = private_roots(tmp_path)
    browser = state_root / "browser"
    browser.mkdir(parents=True)
    browser.chmod(0o755)
    state_root.chmod(0o700)
    (browser / ".securedrop-version").write_text("15.0.19\n")
    (browser / ".securedrop-version").chmod(0o600)
    retired = state_root / ".retired-crashed"
    retired.mkdir()
    retired.chmod(0o755)
    (retired / ".securedrop-version").write_text("15.0.18\n")
    (retired / ".securedrop-version").chmod(0o600)
    abandoned_profile = runtime_root / "profile"
    abandoned_profile.mkdir(parents=True)
    runtime_root.chmod(0o700)
    (abandoned_profile / "cookies.sqlite").write_text("session state")

    with lifecycle.exclusive_lifecycle(state_root, runtime_root):
        assert browser.is_dir()
        assert not retired.exists()
        assert not abandoned_profile.exists()


def test_ambiguous_interrupted_replacement_fails_closed(tmp_path: Path) -> None:
    state_root, runtime_root = private_roots(tmp_path)
    (state_root / ".retired-one").mkdir(parents=True)
    (state_root / ".retired-one").chmod(0o755)
    state_root.chmod(0o700)
    (state_root / ".retired-two").mkdir()
    (state_root / ".retired-two").chmod(0o755)

    with (
        pytest.raises(OSError, match="multiple retired"),
        lifecycle.exclusive_lifecycle(state_root, runtime_root),
    ):
        pytest.fail("ambiguous state must not launch")


@pytest.mark.parametrize("unsafe", ["symlink", "permissions", "file", "owner"])
def test_unsafe_durable_root_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    unsafe: str,
) -> None:
    state_root, runtime_root = private_roots(tmp_path)
    if unsafe == "symlink":
        target = tmp_path / "target"
        target.mkdir()
        state_root.symlink_to(target)
    elif unsafe == "file":
        state_root.write_text("not a directory")
    else:
        state_root.mkdir()
        if unsafe == "permissions":
            state_root.chmod(0o755)
        else:
            real_lstat = lifecycle.os.lstat

            def wrong_owner(path: Path) -> os.stat_result:
                result = real_lstat(path)
                if Path(path) == state_root:
                    values = list(result)
                    values[4] = result.st_uid + 1
                    return os.stat_result(values)
                return result

            monkeypatch.setattr(lifecycle.os, "lstat", wrong_owner)

    with (
        pytest.raises(OSError, match="unsafe"),
        lifecycle.exclusive_lifecycle(state_root, runtime_root),
    ):
        pytest.fail("unsafe root must not launch")


def test_symlinked_durable_parent_fails_closed(tmp_path: Path) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent)
    state_root = linked_parent / "state"
    state_root.mkdir(mode=0o700)
    runtime_root = tmp_path / "runtime"

    with (
        pytest.raises(OSError, match="unsafe"),
        lifecycle.exclusive_lifecycle(state_root, runtime_root),
    ):
        pytest.fail("a symlinked parent must not redirect durable state")


def test_writable_durable_parent_fails_closed(tmp_path: Path) -> None:
    writable_parent = tmp_path / "writable-parent"
    writable_parent.mkdir(mode=0o777)
    writable_parent.chmod(0o777)
    state_root = writable_parent / "state"
    state_root.mkdir(mode=0o700)

    with (
        pytest.raises(OSError, match="parent directory"),
        lifecycle.exclusive_lifecycle(state_root, tmp_path / "runtime"),
    ):
        pytest.fail("a writable parent must not permit root replacement")


@pytest.mark.parametrize("name", ["browser", "highest-version"])
@pytest.mark.parametrize("unsafe", ["symlink", "permissions", "file-type", "owner"])
def test_unsafe_durable_entries_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    unsafe: str,
) -> None:
    state_root, runtime_root = private_roots(tmp_path)
    state_root.mkdir(mode=0o700)
    entry = state_root / name
    expected_directory = name == "browser"
    if unsafe == "symlink":
        target = tmp_path / "attacker-controlled"
        target.mkdir()
        entry.symlink_to(target)
    elif unsafe == "file-type":
        if expected_directory:
            entry.write_text("not a browser directory")
        else:
            entry.mkdir()
    else:
        if expected_directory:
            entry.mkdir(mode=0o700)
        else:
            entry.write_text("15.0.19\n")
            entry.chmod(0o600)
        if unsafe == "permissions":
            entry.chmod(0o777 if expected_directory else 0o644)
        else:
            real_lstat = lifecycle.os.lstat

            def wrong_owner(path: Path) -> os.stat_result:
                result = real_lstat(path)
                if Path(path) == entry:
                    values = list(result)
                    values[4] = result.st_uid + 1
                    return os.stat_result(values)
                return result

            monkeypatch.setattr(lifecycle.os, "lstat", wrong_owner)

    with (
        pytest.raises(OSError, match="unsafe"),
        lifecycle.exclusive_lifecycle(state_root, runtime_root),
    ):
        pytest.fail("unsafe durable entry must not launch")


@pytest.mark.parametrize("unsafe", ["symlink", "permissions", "file", "owner"])
def test_unsafe_runtime_root_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    unsafe: str,
) -> None:
    state_root, runtime_root = private_roots(tmp_path)
    if unsafe == "symlink":
        target = tmp_path / "runtime-target"
        target.mkdir()
        runtime_root.symlink_to(target)
    elif unsafe == "file":
        runtime_root.write_text("not a directory")
    else:
        runtime_root.mkdir(parents=True)
        if unsafe == "permissions":
            runtime_root.chmod(0o755)
        else:
            runtime_root.chmod(0o700)
            real_lstat = lifecycle.os.lstat

            def wrong_owner(path: Path) -> os.stat_result:
                result = real_lstat(path)
                if Path(path) == runtime_root:
                    values = list(result)
                    values[4] = result.st_uid + 1
                    return os.stat_result(values)
                return result

            monkeypatch.setattr(lifecycle.os, "lstat", wrong_owner)

    with (
        pytest.raises(OSError, match="unsafe"),
        lifecycle.exclusive_lifecycle(state_root, runtime_root),
    ):
        pytest.fail("unsafe runtime root must not launch")
