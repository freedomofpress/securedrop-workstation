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

# Fixtures (sample files) for certain tests
FIXTURES_PATH = Path(__file__).parent / "fixtures"


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
