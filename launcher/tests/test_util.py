import os
import pytest
import re
import subprocess

from unittest import mock
from importlib.machinery import SourceFileLoader
from tempfile import TemporaryDirectory

# Regex for lock conflicts
BUSY_LOCK_REGEX = r"Error obtaining lock on '.*'."

# Regex for failure to obtain lock due to permission error
LOCK_PERMISSION_REGEX = r"Error writing to lock file '.*'"

CONFLICTING_PROCESS_REGEX = r"Conflicting process .* is currently running."

# Fixtures (sample files) for certain tests
FIXTURES_PATH = os.path.join(os.path.dirname(__file__), "fixtures")

relpath_util = "../sdw_util/Util.py"
path_to_util = os.path.join(os.path.dirname(os.path.abspath(__file__)), relpath_util)
util = SourceFileLoader("Util", path_to_util).load_module()


@mock.patch("Util.sdlog.error")
@mock.patch("Util.sdlog.warning")
@mock.patch("Util.sdlog.info")
def test_obtain_lock(mocked_info, mocked_warning, mocked_error):
    """
    Test whether we can successfully obtain an exclusive lock
    """
    with TemporaryDirectory() as tmpdir, mock.patch("Util.LOCK_DIRECTORY", tmpdir):

        basename = "test-obtain-lock.lock"
        pid = os.getpid()
        lh = util.obtain_lock(basename)  # noqa: F841
        # No handled exception should occur
        assert not mocked_error.called
        # We should be getting a lock handle back
        assert lh is not None

        cmd = ["lsof", "-w", os.path.join(util.LOCK_DIRECTORY, basename)]
        output_lines = subprocess.check_output(cmd).decode("utf-8").strip().split("\n")
        # We expect exactly one process to be accessing this file, plus output header
        assert len(output_lines) == 2
        lsof_data = output_lines[1].split()
        # We expect the output to have the standard number of fields
        assert len(lsof_data) == 9
        # We expect the PID column to contain the ID of this process
        assert lsof_data[1] == str(pid)
        # We expect an exclusive write lock to be set for this process
        assert lsof_data[3].find("W") != -1


@mock.patch("Util.sdlog.error")
@mock.patch("Util.sdlog.warning")
@mock.patch("Util.sdlog.info")
def test_cannot_obtain_exclusive_lock_when_busy(mocked_info, mocked_warning, mocked_error):
    """
    Test whether only a single process can obtan an exclusive lock (basic
    lockfile behavior).

    This is used to prevent multiple preflight updaters or multiple notifiers
    from being instantiated.
    """
    with TemporaryDirectory() as tmpdir, mock.patch("Util.LOCK_DIRECTORY", tmpdir):

        basename = "test-exclusive-lock.lock"
        lh1 = util.obtain_lock(basename)  # noqa: F841

        # We're running in the same process, so obtaining a lock will succeed.
        # Instead we're mocking the IOError lockf would raise.
        with mock.patch("fcntl.lockf", side_effect=IOError()) as mocked_lockf:
            lh2 = util.obtain_lock(basename)
            mocked_lockf.assert_called_once()
            assert lh2 is None
            error_string = mocked_error.call_args[0][0]
            assert re.search(BUSY_LOCK_REGEX, error_string) is not None


@mock.patch("Util.sdlog.error")
@mock.patch("Util.sdlog.warning")
@mock.patch("Util.sdlog.info")
def test_cannot_obtain_shared_lock_when_busy(mocked_info, mocked_warning, mocked_error):
    """
    Test whether an exlusive lock on a lock file is successfully detected
    by means of attempting to obtain a shared, nonexclusive lock on the same
    file.

    In the preflight updater / notifier, this is used to prevent the notification
    from being displayed when the preflight updater is already open.
    """
    with TemporaryDirectory() as tmpdir, mock.patch("Util.LOCK_DIRECTORY", tmpdir):

        basename = "test-conflict.lock"
        lh = util.obtain_lock(basename)  # noqa: F841

        # We're running in the same process, so obtaining a lock will succeed.
        # Instead we're mocking the IOError lockf would raise.
        with mock.patch("fcntl.lockf", side_effect=IOError()) as mocked_lockf:
            can_get_lock = util.can_obtain_lock(basename)
            mocked_lockf.assert_called_once()
            assert can_get_lock is False
            error_string = mocked_error.call_args[0][0]
            assert re.search(BUSY_LOCK_REGEX, error_string) is not None


@mock.patch("Util.sdlog.error")
@mock.patch("Util.sdlog.warning")
@mock.patch("Util.sdlog.info")
def test_no_lockfile_no_problems(mocked_info, mocked_warning, mocked_error):
    """
    Test whether our shared lock test succeeds even when there's no lockfile
    (which means the process has not run recently, or ever, and it's safe to
    run the potentially conflicting process).
    """
    with TemporaryDirectory() as tmpdir, mock.patch("Util.LOCK_DIRECTORY", tmpdir):
        lock_result = util.can_obtain_lock("404.lock")
        assert lock_result is True


@mock.patch("Util.sdlog.error")
@mock.patch("Util.sdlog.warning")
@mock.patch("Util.sdlog.info")
def test_permission_error_is_handled(mocked_info, mocked_warning, mocked_error):
    """
    Test whether permission errors obtaining a lock are handled correctly
    """
    with mock.patch("builtins.open", side_effect=PermissionError()) as mocked_open:  # noqa: F821
        lock = util.obtain_lock("test-open-error.lock")
        assert lock is None
        mocked_open.assert_called_once()
        mocked_error.assert_called_once()
        error_string = mocked_error.call_args[0][0]
        assert re.search(LOCK_PERMISSION_REGEX, error_string) is not None


@mock.patch("Util.sdlog.error")
@mock.patch("Util.sdlog.warning")
@mock.patch("Util.sdlog.info")
def test_stale_lockfile_has_no_effect(mocked_info, mocked_warning, mocked_error):
    """
    Test whether we can get a shared lock when a lockfile exists, but nobody
    is accessing it.
    """
    with TemporaryDirectory() as tmpdir, mock.patch("Util.LOCK_DIRECTORY", tmpdir):

        # Because we're not assigning the return value, it will be immediately released
        basename = "test-stale.lock"
        util.obtain_lock(basename)
        lock_result = util.can_obtain_lock(basename)
        assert lock_result is True


def test_log():
    """
    Test whether we can successfully write to a log file
    """
    with TemporaryDirectory() as tmpdir, mock.patch("Util.LOG_DIRECTORY", tmpdir):
        basename = "test.log"
        # configure_logging is expected to re-create the directory.
        os.rmdir(tmpdir)
        util.configure_logging(basename)
        util.sdlog.info("info level log entry")
        util.sdlog.warning("error level log entry")
        util.sdlog.error("error level log entry")
        path = os.path.join(tmpdir, basename)
        count = len(open(path).readlines())
        assert count == 3


@pytest.mark.parametrize(
    "return_code,expected_result", [(0, True), (1, False)],
)
@mock.patch("Util.sdlog.error")
@mock.patch("Util.sdlog.warning")
@mock.patch("Util.sdlog.info")
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
        running_process = util.is_conflicting_process_running(["cowsay"])
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
    "os_release_fixture,version_contains",
    [
        ("os-release-qubes-4.0", "4.0"),
        ("os-release-qubes-4.1", "4.1"),
        ("os-release-ubuntu", None),
        ("no-such-file", None),
    ],
)
@mock.patch("Util.sdlog.error")
@mock.patch("Util.sdlog.warning")
@mock.patch("Util.sdlog.info")
@mock.patch("Util.OS_RELEASE_FILE", os.path.join(FIXTURES_PATH, "os-release-qubes-4.0"))
def test_detect_qubes(
    mocked_info, mocked_warning, mocked_error, os_release_fixture, version_contains
):
    """
    Test whether we can successfully detect whether we're on Qubes and, if so,
    what version of Qubes, by parsing /etc/os-release in the expected format.
    """
    with mock.patch("Util.OS_RELEASE_FILE", os.path.join(FIXTURES_PATH, os_release_fixture)):
        qubes_version = util.get_qubes_version()
        if version_contains is not None:
            assert qubes_version is not None
            assert version_contains in qubes_version
        else:
            assert qubes_version is None


@pytest.mark.parametrize(
    "env_override,expected_qt_override_result", [(None, None), ("4", 4), ("5", 5)]
)
@pytest.mark.parametrize(
    "os_release_fixture,expected_qt_version",
    [
        ("os-release-qubes-4.0", 4),
        ("os-release-qubes-4.1", 5),
        ("os-release-ubuntu", 4),
        ("no-such-file", 4),
    ],
)
@mock.patch("Util.sdlog.error")
@mock.patch("Util.sdlog.warning")
@mock.patch("Util.sdlog.info")
@mock.patch("Util.OS_RELEASE_FILE", os.path.join(FIXTURES_PATH, "os-release-qubes-4.0"))
def test_pick_qt(
    mocked_info,
    mocked_warning,
    mocked_error,
    os_release_fixture,
    expected_qt_version,
    env_override,
    expected_qt_override_result,
):
    """
    Test whether we're using the expected Qt version based on the operating system
    and the environment variable, which should take precedence if defined.
    """
    if env_override is None:
        mocked_env = {}
    else:
        mocked_env = {"SDW_UPDATER_QT": env_override}

    with mock.patch(
        "Util.OS_RELEASE_FILE", os.path.join(FIXTURES_PATH, os_release_fixture)
    ), mock.patch.dict("os.environ", mocked_env):
        qt_version = util.get_qt_version()
        if expected_qt_override_result is not None:
            assert qt_version == expected_qt_override_result
        else:
            assert qt_version == expected_qt_version


@pytest.mark.parametrize("env_override", ["3", "3000", "GTK"])
@mock.patch("Util.sdlog.error")
@mock.patch("Util.sdlog.warning")
@mock.patch("Util.sdlog.info")
def test_pick_bad_qt(
    mocked_info, mocked_warning, mocked_error, env_override,
):
    """
    Test whether we're getting the expected error when specifying an invalid
    version via environment override
    """
    mocked_env = {"SDW_UPDATER_QT": env_override}
    with mock.patch.dict("os.environ", mocked_env), pytest.raises(ValueError):
        util.get_qt_version()
