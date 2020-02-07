import datetime
import os
import pytest
import re
import subprocess

from unittest import mock
from importlib.machinery import SourceFileLoader
from multiprocessing import Pool
from tempfile import TemporaryDirectory

relpath_notify = "../sdw_notify/Notify.py"
path_to_notify = os.path.join(os.path.dirname(os.path.abspath(__file__)), relpath_notify)
notify = SourceFileLoader("Notify", path_to_notify).load_module()

relpath_updater = "../sdw_updater_gui/Updater.py"
path_to_updater = os.path.join(os.path.dirname(os.path.abspath(__file__)), relpath_updater)
updater = SourceFileLoader("Updater", path_to_updater).load_module()

# Regex for warning log if we have no successful update, but uptime is below threshold
UPTIME_WARNING_REGEX = r"^Uptime \(.* hours\) is above warning threshold \(.* hours\)."

# Regex for warning log if we've updated too long ago, and grace period has elapsed
UPDATER_WARNING_REGEX = r"^Last successful update \(.* hours ago\) is above warning threshold "
r"\(.* hours\). Uptime grace period of .* hours has elapsed (uptime: .* hours)."

# Regex for info log if we've updated too long ago, but grace period still ticking
GRACE_PERIOD_REGEX = r"Last successful update \(.* hours ago\) is above "
r"warning threshold \(.* hours\). Uptime grace period of .* hours has not elapsed "
r"yet \(uptime: .* hours\)."

# Regex for info log if we've updated recently enough
NO_WARNING_REGEX = r"Last successful update \(.* hours ago\) is below the warning threshold "
r"\(.* hours\)."

BAD_TIMESTAMP_REGEX = r"Data in .* not in the expected format."


@mock.patch("Notify.sdlog.error")
@mock.patch("Notify.sdlog.warning")
@mock.patch("Notify.sdlog.info")
def test_notify_lock(
        mocked_info, mocked_warning, mocked_error
):
    """
    Test whether we can successfully obtain an exclusive lock for the notifier
    script
    """
    with TemporaryDirectory() as tmpdir:
        notify.LOCK_FILE_NOTIFIER = os.path.join(tmpdir, "sdw-launcher.lock")
        pid = os.getpid()
        lh = notify.obtain_notify_lock()  # noqa: F841
        # No handled exception should occur
        assert not mocked_error.called
        # We should be getting a lock handle back
        assert lh is not None

        cmd = ['lsof', '-w', notify.LOCK_FILE_NOTIFIER]
        output_lines = subprocess.check_output(cmd).decode("utf-8").strip().split('\n')
        # We expect exactly one process to be accessing this file, plus output header
        assert len(output_lines) == 2
        lsof_data = output_lines[1].split()
        # We expect the output to have the standard number of fields
        assert len(lsof_data) == 9
        # We expect the PID column to contain the ID of this process
        assert lsof_data[1] == str(pid)
        # We expect an exclusive write lock to be set for this process
        assert lsof_data[3].find('W') != -1


@mock.patch("Notify.sdlog.error")
@mock.patch("Notify.sdlog.warning")
@mock.patch("Notify.sdlog.info")
def test_updater_lock_prevents_notifier(
    mocked_info, mocked_warning, mocked_error
):
    """
    Test whether an exlusive lock on the updater lock file prevents the notifier
    from launching (so it does not come up when the user is in the process of
    updating).
    """
    with TemporaryDirectory() as tmpdir:
        notify.LOCK_FILE_LAUNCHER = os.path.join(tmpdir, "sdw-launcher.lock")
        updater.LOCK_FILE = os.path.join(tmpdir, "sdw-launcher.lock")
        lh = updater.obtain_lock()  # noqa: F841

        # We're in the same process, so obtaining an additional lock would
        # always succeed. We use the multiprocessing module to run the function
        # as a separate process.
        p = Pool(processes=1)
        lock_result = p.apply(notify.can_obtain_updater_lock)
        p.close()
        assert lock_result is False


@mock.patch("Notify.sdlog.error")
@mock.patch("Notify.sdlog.warning")
@mock.patch("Notify.sdlog.info")
def test_no_updater_lock_has_no_effect(
        mocked_info, mocked_warning, mocked_error
):
    """
    Test whether we _can_ run the notifier when we don't have a lock
    on the updater.
    """
    with TemporaryDirectory() as tmpdir:
        notify.LOCK_FILE_LAUNCHER = os.path.join(tmpdir, "sdw-launcher.lock")
        lock_result = notify.can_obtain_updater_lock()
        assert lock_result is True


@mock.patch("Notify.get_uptime_seconds", return_value=notify.WARNING_THRESHOLD + 1)
@mock.patch("Notify.sdlog.error")
@mock.patch("Notify.sdlog.warning")
@mock.patch("Notify.sdlog.info")
def test_warning_shown_if_uptime_exceeded_and_updater_never_ran(
        mocked_info, mocked_warning, mocked_error, mocked_uptime
):
    """
    Test whether we're correctly going to show a warning if the uptime exceeds
    the warning threshold and the updater has never run
    """
    with TemporaryDirectory() as tmpdir:
        # We're going to look for a nonexistent file in an existing tmpdir
        notify.LAST_UPDATED_FILE = os.path.join(tmpdir, "file-does-not-exist")
        warning_should_be_shown = notify.is_update_check_necessary()

        assert warning_should_be_shown is True
        # No handled errors should occur
        assert not mocked_error.called
        # A warning should also be logged
        mocked_warning.assert_called_once()
        # Ensure warning matches expected output
        warning_string = mocked_warning.call_args[0][0]
        assert re.search(UPTIME_WARNING_REGEX, warning_string) is not None


@pytest.mark.parametrize("uptime,warning_expected", [
                        (notify.UPTIME_GRACE_PERIOD + 1, True),
                        (notify.UPTIME_GRACE_PERIOD - 1, False)
])
@mock.patch("Notify.sdlog.error")
@mock.patch("Notify.sdlog.warning")
@mock.patch("Notify.sdlog.info")
def test_warning_shown_if_warning_threshold_exceeded(
        mocked_info, mocked_warning, mocked_error, uptime, warning_expected
):
    """
    Primary use case for the notifier: are we showing the warning if the
    system hasn't been (successfully) updated for longer than the warning
    threshold? Expected result varies based on whether system uptime exceeds
    a grace period (for the user to launch the app on their own).
    """
    with TemporaryDirectory() as tmpdir:
        # Write a "last successfully updated" date well in the past for check
        notify.LAST_UPDATED_FILE = os.path.join(tmpdir, "sdw-last-updated")
        historic_date = datetime.date(2013, 6, 5).strftime(updater.DATE_FORMAT)
        with open(notify.LAST_UPDATED_FILE, "w") as f:
            f.write(historic_date)

        with mock.patch("Notify.get_uptime_seconds") as mocked_uptime:
            mocked_uptime.return_value = uptime
            warning_should_be_shown = notify.is_update_check_necessary()
        assert warning_should_be_shown is warning_expected
        # No handled errors should occur
        assert not mocked_error.called
        # A warning should also be logged
        if warning_expected is True:
            mocked_warning.assert_called_once()
            warning_string = mocked_warning.call_args[0][0]
            assert re.search(UPDATER_WARNING_REGEX, warning_string) is not None
        else:
            assert not mocked_warning.called
            mocked_info.assert_called_once()
            info_string = mocked_info.call_args[0][0]
            assert re.search(GRACE_PERIOD_REGEX, info_string) is not None


@mock.patch("Notify.sdlog.error")
@mock.patch("Notify.sdlog.warning")
@mock.patch("Notify.sdlog.info")
def test_warning_not_shown_if_warning_threshold_not_exceeded(
    mocked_info, mocked_warning, mocked_error
):
    """
    Another high priority case: we don't want to warn the user if they've
    recently run the updater successfully.
    """
    with TemporaryDirectory() as tmpdir:
        # Write current timestamp into the file
        notify.LAST_UPDATED_FILE = os.path.join(tmpdir, "sdw-last-updated")
        just_now = datetime.datetime.now().strftime(updater.DATE_FORMAT)
        with open(notify.LAST_UPDATED_FILE, "w") as f:
            f.write(just_now)
        warning_should_be_shown = notify.is_update_check_necessary()
        assert warning_should_be_shown is False
        assert not mocked_error.called
        assert not mocked_warning.called
        info_string = mocked_info.call_args[0][0]
        assert re.search(NO_WARNING_REGEX, info_string) is not None


@mock.patch("Notify.sdlog.error")
@mock.patch("Notify.sdlog.warning")
@mock.patch("Notify.sdlog.info")
def test_corrupt_timestamp_file_handled(
    mocked_info, mocked_warning, mocked_error
):
    """
    The LAST_UPDATED_FILE must contain a timestamp in a specified format;
    if it doesn't, we return None and log the error.
    """
    with TemporaryDirectory() as tmpdir:
        notify.LAST_UPDATED_FILE = os.path.join(tmpdir, "sdw-last-updated")
        with open(notify.LAST_UPDATED_FILE, "w") as f:
            # With apologies to HAL 9000
            f.write("daisy, daisy, give me your answer do")
        warning_should_be_shown = notify.is_update_check_necessary()
        assert warning_should_be_shown is None
        mocked_error.assert_called_once()
        error_string = mocked_error.call_args[0][0]
        assert re.search(BAD_TIMESTAMP_REGEX, error_string) is not None


def test_uptime_is_sane():
    """
    Even in a CI container this should be greater than zero :-)
    """
    seconds = notify.get_uptime_seconds()
    assert isinstance(seconds, float)
    assert seconds > 0
