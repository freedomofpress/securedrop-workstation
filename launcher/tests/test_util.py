import os
import re
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from sdw_util import Util

# Regex for lock conflicts
BUSY_LOCK_REGEX = r"Error obtaining lock on '.*'."

# Regex for failure to obtain lock due to permission error
LOCK_PERMISSION_REGEX = r"Error writing to lock file '.*'"

CONFLICTING_PROCESS_REGEX = r"Conflicting process .* is currently running."

# Fixtures (sample files) for certain tests
FIXTURES_PATH = Path(__file__).parent / "fixtures"

DEBIAN_VERSION = "bookworm"


@mock.patch("sdw_util.Util.sdlog.error")
@mock.patch("sdw_util.Util.sdlog.warning")
@mock.patch("sdw_util.Util.sdlog.info")
def test_obtain_lock(mocked_info, mocked_warning, mocked_error, tmp_path):
    """
    Test whether we can successfully obtain an exclusive lock
    """
    with mock.patch("sdw_util.Util.LOCK_DIRECTORY", tmp_path):
        basename = "test-obtain-lock.lock"
        pid_str = str(os.getpid())
        lh = Util.obtain_lock(basename)
        # No handled exception should occur
        assert not mocked_error.called
        # We should be getting a lock handle back
        assert lh is not None

        # Note that there are different lock types; lslocks provides information
        # about all of them for a given process, including POSIX system locks,
        # which is the type we want to verify.
        lslocks_output = (
            subprocess.check_output(["lslocks", "-n", "-p", pid_str]).decode("utf-8").strip()
        )

        # Due to output discrepancies between local tests and CI these assertions
        # are naive, but sufficient for the purposes of this test suite, as no
        # write locks other than the test-created ones should be present.
        assert "WRITE" in lslocks_output
        assert "POSIX" in lslocks_output


@mock.patch("sdw_util.Util.sdlog.error")
@mock.patch("sdw_util.Util.sdlog.warning")
@mock.patch("sdw_util.Util.sdlog.info")
def test_cannot_obtain_exclusive_lock_when_busy(
    mocked_info, mocked_warning, mocked_error, tmp_path
):
    """
    Test whether only a single process can obtan an exclusive lock (basic
    lockfile behavior).

    This is used to prevent multiple preflight updaters or multiple notifiers
    from being instantiated.
    """
    with mock.patch("sdw_util.Util.LOCK_DIRECTORY", tmp_path):
        basename = "test-exclusive-lock.lock"
        Util.obtain_lock(basename)

        # We're running in the same process, so obtaining a lock will succeed.
        # Instead we're mocking the IOError lockf would raise.
        with mock.patch("fcntl.lockf", side_effect=OSError()) as mocked_lockf:
            lh2 = Util.obtain_lock(basename)
            mocked_lockf.assert_called_once()
            assert lh2 is None
            error_string = mocked_error.call_args[0][0]
            assert re.search(BUSY_LOCK_REGEX, error_string) is not None


@mock.patch("sdw_util.Util.sdlog.error")
@mock.patch("sdw_util.Util.sdlog.warning")
@mock.patch("sdw_util.Util.sdlog.info")
def test_cannot_obtain_shared_lock_when_busy(mocked_info, mocked_warning, mocked_error, tmp_path):
    """
    Test whether an exlusive lock on a lock file is successfully detected
    by means of attempting to obtain a shared, nonexclusive lock on the same
    file.

    In the preflight updater / notifier, this is used to prevent the notification
    from being displayed when the preflight updater is already open.
    """
    with mock.patch("sdw_util.Util.LOCK_DIRECTORY", tmp_path):
        basename = "test-conflict.lock"
        Util.obtain_lock(basename)

        # We're running in the same process, so obtaining a lock will succeed.
        # Instead we're mocking the IOError lockf would raise.
        with mock.patch("fcntl.lockf", side_effect=OSError()) as mocked_lockf:
            can_get_lock = Util.can_obtain_lock(basename)
            mocked_lockf.assert_called_once()
            assert can_get_lock is False
            error_string = mocked_error.call_args[0][0]
            assert re.search(BUSY_LOCK_REGEX, error_string) is not None


@mock.patch("sdw_util.Util.sdlog.error")
@mock.patch("sdw_util.Util.sdlog.warning")
@mock.patch("sdw_util.Util.sdlog.info")
def test_no_lockfile_no_problems(mocked_info, mocked_warning, mocked_error, tmp_path):
    """
    Test whether our shared lock test succeeds even when there's no lockfile
    (which means the process has not run recently, or ever, and it's safe to
    run the potentially conflicting process).
    """
    with mock.patch("sdw_util.Util.LOCK_DIRECTORY", tmp_path):
        lock_result = Util.can_obtain_lock("404.lock")
        assert lock_result is True


@mock.patch("sdw_util.Util.sdlog.error")
@mock.patch("sdw_util.Util.sdlog.warning")
@mock.patch("sdw_util.Util.sdlog.info")
def test_permission_error_is_handled(mocked_info, mocked_warning, mocked_error):
    """
    Test whether permission errors obtaining a lock are handled correctly
    """
    with mock.patch("builtins.open", side_effect=PermissionError()) as mocked_open:
        lock = Util.obtain_lock("test-open-error.lock")
        assert lock is None
        mocked_open.assert_called_once()
        mocked_error.assert_called_once()
        error_string = mocked_error.call_args[0][0]
        assert re.search(LOCK_PERMISSION_REGEX, error_string) is not None


@mock.patch("sdw_util.Util.sdlog.error")
@mock.patch("sdw_util.Util.sdlog.warning")
@mock.patch("sdw_util.Util.sdlog.info")
def test_stale_lockfile_has_no_effect(mocked_info, mocked_warning, mocked_error, tmp_path):
    """
    Test whether we can get a shared lock when a lockfile exists, but nobody
    is accessing it.
    """
    with mock.patch("sdw_util.Util.LOCK_DIRECTORY", tmp_path):
        # Because we're not assigning the return value, it will be immediately released
        basename = "test-stale.lock"
        Util.obtain_lock(basename)
        lock_result = Util.can_obtain_lock(basename)
        assert lock_result is True


def test_log(tmp_path):
    """
    Test whether we can successfully write to a log file
    """
    with mock.patch("sdw_util.Util.LOG_DIRECTORY", tmp_path):
        basename = "test.log"
        # configure_logging is expected to re-create the directory.
        os.rmdir(tmp_path)
        Util.configure_logging(basename)
        Util.sdlog.info("info level log entry")
        Util.sdlog.warning("error level log entry")
        Util.sdlog.error("error level log entry")
        path = tmp_path / basename
        count = len(path.open().readlines())
        assert count == 3


@pytest.mark.parametrize(("return_code", "expected_result"), [(0, True), (1, False)])
@mock.patch("sdw_util.Util.sdlog.error")
@mock.patch("sdw_util.Util.sdlog.warning")
@mock.patch("sdw_util.Util.sdlog.info")
def test_for_conflicting_process(
    mocked_info, mocked_warning, mocked_error, return_code, expected_result
):
    """
    Test whether we can successfully detect conflicting processes.
    """
    # We mock the pgrep call itself, which means we _won't_ detect behavior
    # changes at that level.
    completed_process = subprocess.CompletedProcess(args=[], returncode=return_code)
    with mock.patch("subprocess.run", return_value=completed_process) as mocked_run:
        running_process = Util.is_conflicting_process_running(["cowsay"])
        mocked_run.assert_called_once()
        if expected_result is True:
            assert running_process is True
            mocked_error.assert_called_once()
            error_string = mocked_error.call_args[0][0]
            assert re.search(CONFLICTING_PROCESS_REGEX, error_string) is not None
        else:
            assert running_process is False
            assert not mocked_error.called


@pytest.mark.parametrize(
    ("os_release_fixture", "version_contains"),
    [
        ("os-release-qubes-4.1", "4.1"),
        ("os-release-ubuntu", None),
        ("no-such-file", None),
    ],
)
@mock.patch("sdw_util.Util.sdlog.error")
@mock.patch("sdw_util.Util.sdlog.warning")
@mock.patch("sdw_util.Util.sdlog.info")
@mock.patch("sdw_util.Util.OS_RELEASE_FILE", FIXTURES_PATH / "os-release-qubes-4.1")
def test_detect_qubes(
    mocked_info, mocked_warning, mocked_error, os_release_fixture, version_contains
):
    """
    Test whether we can successfully detect whether we're on Qubes and, if so,
    what version of Qubes, by parsing /etc/os-release in the expected format.
    """
    with mock.patch("sdw_util.Util.OS_RELEASE_FILE", FIXTURES_PATH / os_release_fixture):
        qubes_version = Util.get_qubes_version()
        if version_contains is not None:
            assert qubes_version is not None
            assert version_contains in qubes_version
        else:
            assert qubes_version is None


def test_get_logger():
    """
    Test whether the logging utility functions returns namespaced loggers in
    the `prefix.module` format.
    """
    test_prefix = "potato"
    test_module = "salad"
    logger = Util.get_logger(prefix=test_prefix)
    assert logger.name == test_prefix
    logger = Util.get_logger(prefix=test_prefix, module=test_module)
    assert logger.name == f"{test_prefix}.{test_module}"


@pytest.mark.parametrize(
    ("os_release_fixture", "version_contains"),
    [
        ("os-release-qubes-4.1", "4.1"),
        ("os-release-ubuntu", None),
        ("no-such-file", None),
    ],
)
@mock.patch("sdw_util.Util.OS_RELEASE_FILE", FIXTURES_PATH / "os-release-qubes-4.1")
def test_is_sdapp_halted_yes(os_release_fixture, version_contains):
    """
    When sd-app state is 'Halted'
    Then `Util.is_sdapp_halted()` should return True
    """
    output = bytes(
        "NAME     STATE     CLASS     LABEL     TEMPLATE\nsd-app"
        f"    Halted    AppVM   yellow     sd-small-{DEBIAN_VERSION}-template\n",
        "utf-8",
    )

    with mock.patch("subprocess.check_output") as patched_subprocess_check:
        patched_subprocess_check.return_value = output
        assert Util.is_sdapp_halted()


@pytest.mark.parametrize(
    ("os_release_fixture", "version_contains"),
    [
        ("os-release-qubes-4.1", "4.1"),
        ("os-release-ubuntu", None),
        ("no-such-file", None),
    ],
)
@mock.patch("sdw_util.Util.OS_RELEASE_FILE", FIXTURES_PATH / "os-release-qubes-4.1")
def test_is_sdapp_halted_no(os_release_fixture, version_contains):
    """
    When sd-app is not Halted (i.e. Running, Pasued)
    Then Util.is_sd_app_halted() should return False
    """
    output = bytes(
        "NAME     STATE     CLASS     LABEL     TEMPLATE\nsd-app"
        f"    Paused    AppVM   yellow     sd-small-{DEBIAN_VERSION}-template\n",
        "utf-8",
    )

    with mock.patch("subprocess.check_output") as patched_subprocess:
        patched_subprocess.return_value = output
        assert not Util.is_sdapp_halted()


@pytest.mark.parametrize(
    ("os_release_fixture", "version_contains"),
    [
        ("os-release-qubes-4.1", "4.1"),
        ("os-release-ubuntu", None),
        ("no-such-file", None),
    ],
)
@mock.patch("sdw_util.Util.OS_RELEASE_FILE", FIXTURES_PATH / "os-release-qubes-4.1")
@mock.patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "check_output"))
def test_is_sdapp_halted_error(patched_subprocess, os_release_fixture, version_contains):
    """
    When the sd-app status check encounters an error
    Then the call to Util.is_sdapp_halted() should still complete
     And the method should return False
    """

    assert not Util.is_sdapp_halted()
