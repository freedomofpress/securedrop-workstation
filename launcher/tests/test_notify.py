import datetime
import os
import re
from importlib.machinery import SourceFileLoader
from tempfile import TemporaryDirectory
from unittest import mock

import pytest

relpath_notify = "../sdw_notify/Notify.py"
path_to_notify = os.path.join(os.path.dirname(os.path.abspath(__file__)), relpath_notify)
notify = SourceFileLoader("Notify", path_to_notify).load_module()

relpath_updater = "../sdw_updater/Updater.py"
path_to_updater = os.path.join(os.path.dirname(os.path.abspath(__file__)), relpath_updater)
updater = SourceFileLoader("Updater", path_to_updater).load_module()


# Regex for warning log if the last-updated timestamp does not exist (updater
# has never run)
NO_TIMESTAMP_REGEX = r"Timestamp file '.*' does not exist."

# Regex for warning log if we've updated too long ago, and grace period has elapsed
UPDATER_WARNING_REGEX = (
    r"^Last successful update \(.* hours ago\) is above warning threshold "
    r"\(.* hours\). Uptime grace period of .* hours has elapsed \(uptime: .* hours\)."
)

# Regex for info log if we've updated too long ago, but grace period still ticking
GRACE_PERIOD_REGEX = (
    r"Last successful update \(.* hours ago\) is above "
    r"warning threshold \(.* hours\). Uptime grace period of .* hours has not elapsed "
    r"yet \(uptime: .* hours\)."
)

# Regex for info log if we've updated recently enough
NO_WARNING_REGEX = (
    r"Last successful update \(.* hours ago\) is below the warning threshold " r"\(.* hours\)."
)

# Regex for bad contents in `sdw-last-updated` file
BAD_TIMESTAMP_REGEX = r"Data in .* not in the expected format."


@mock.patch("Notify.sdlog.error")
@mock.patch("Notify.sdlog.warning")
@mock.patch("Notify.sdlog.info")
def test_warning_shown_if_updater_never_ran(mocked_info, mocked_warning, mocked_error):
    """
    Test whether we're correctly going to show a warning if the updater has
    never run.
    """
    # We're going to look for a nonexistent file in an existing tmpdir
    with TemporaryDirectory() as tmpdir, mock.patch(
        "Notify.LAST_UPDATED_FILE", os.path.join(tmpdir, "not-a-file")
    ):

        warning_should_be_shown = notify.is_update_check_necessary()

        # No handled errors should occur
        assert not mocked_error.called

        # We display a warning, because this file should always exist
        assert warning_should_be_shown is True

        # A warning should also be logged
        mocked_warning.assert_called_once()

        # Ensure warning matches expected output
        warning_string = mocked_warning.call_args[0][0]
        assert re.search(NO_TIMESTAMP_REGEX, warning_string) is not None


@pytest.mark.parametrize(
    "uptime,warning_expected",
    [(notify.UPTIME_GRACE_PERIOD + 1, True), (notify.UPTIME_GRACE_PERIOD - 1, False)],
)
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
    with TemporaryDirectory() as tmpdir, mock.patch(
        "Notify.LAST_UPDATED_FILE", os.path.join(tmpdir, "sdw-last-updated")
    ):
        # Write a "last successfully updated" date well in the past for check
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
    with TemporaryDirectory() as tmpdir, mock.patch(
        "Notify.LAST_UPDATED_FILE", os.path.join(tmpdir, "sdw-last-updated")
    ):
        # Write current timestamp into the file
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
def test_corrupt_timestamp_file_handled(mocked_info, mocked_warning, mocked_error):
    """
    The LAST_UPDATED_FILE must contain a timestamp in a specified format;
    if it doesn't, we show the warning and log the error.
    """
    with TemporaryDirectory() as tmpdir, mock.patch(
        "Notify.LAST_UPDATED_FILE", os.path.join(tmpdir, "sdw-last-updated")
    ):
        with open(notify.LAST_UPDATED_FILE, "w") as f:
            # With apologies to HAL 9000
            f.write("daisy, daisy, give me your answer do")
        warning_should_be_shown = notify.is_update_check_necessary()
        assert warning_should_be_shown is True
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
