import datetime
import re
from unittest import mock

import pytest

from sdw_notify import Notify
from sdw_updater import Updater

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


@mock.patch("sdw_notify.Notify.sdlog.error")
@mock.patch("sdw_notify.Notify.sdlog.warning")
@mock.patch("sdw_notify.Notify.sdlog.info")
def test_warning_shown_if_updater_never_ran(mocked_info, mocked_warning, mocked_error, tmp_path):
    """
    Test whether we're correctly going to show a warning if the updater has
    never run.
    """
    # We're going to look for a nonexistent file in an existing temporary directoryr
    with mock.patch("sdw_notify.Notify.LAST_UPDATED_FILE", tmp_path / "not-a-file"):
        warning_should_be_shown = Notify.is_update_check_necessary()

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
    ("uptime", "warning_expected"),
    [(Notify.UPTIME_GRACE_PERIOD + 1, True), (Notify.UPTIME_GRACE_PERIOD - 1, False)],
)
@mock.patch("sdw_notify.Notify.sdlog.error")
@mock.patch("sdw_notify.Notify.sdlog.warning")
@mock.patch("sdw_notify.Notify.sdlog.info")
def test_warning_shown_if_warning_threshold_exceeded(
    mocked_info, mocked_warning, mocked_error, tmp_path, uptime, warning_expected
):
    """
    Primary use case for the notifier: are we showing the warning if the
    system hasn't been (successfully) updated for longer than the warning
    threshold? Expected result varies based on whether system uptime exceeds
    a grace period (for the user to launch the app on their own).
    """
    with mock.patch("sdw_notify.Notify.LAST_UPDATED_FILE", tmp_path / "sdw-last-updated"):
        # Write a "last successfully updated" date well in the past for check
        historic_date = datetime.date(2013, 6, 5).strftime(Updater.DATE_FORMAT)
        with open(Notify.LAST_UPDATED_FILE, "w") as f:
            f.write(historic_date)

        with mock.patch("sdw_notify.Notify.get_uptime_seconds") as mocked_uptime:
            mocked_uptime.return_value = uptime
            warning_should_be_shown = Notify.is_update_check_necessary()
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


@mock.patch("sdw_notify.Notify.sdlog.error")
@mock.patch("sdw_notify.Notify.sdlog.warning")
@mock.patch("sdw_notify.Notify.sdlog.info")
def test_warning_not_shown_if_warning_threshold_not_exceeded(
    mocked_info, mocked_warning, mocked_error, tmp_path
):
    """
    Another high priority case: we don't want to warn the user if they've
    recently run the updater successfully.
    """
    with mock.patch("sdw_notify.Notify.LAST_UPDATED_FILE", tmp_path / "sdw-last-updated"):
        # Write current timestamp into the file
        just_now = datetime.datetime.now().strftime(Updater.DATE_FORMAT)
        with open(Notify.LAST_UPDATED_FILE, "w") as f:
            f.write(just_now)
        warning_should_be_shown = Notify.is_update_check_necessary()
        assert warning_should_be_shown is False
        assert not mocked_error.called
        assert not mocked_warning.called
        info_string = mocked_info.call_args[0][0]
        assert re.search(NO_WARNING_REGEX, info_string) is not None


@mock.patch("sdw_notify.Notify.sdlog.error")
@mock.patch("sdw_notify.Notify.sdlog.warning")
@mock.patch("sdw_notify.Notify.sdlog.info")
def test_corrupt_timestamp_file_handled(mocked_info, mocked_warning, mocked_error, tmp_path):
    """
    The LAST_UPDATED_FILE must contain a timestamp in a specified format;
    if it doesn't, we show the warning and log the error.
    """
    with mock.patch("sdw_notify.Notify.LAST_UPDATED_FILE", tmp_path / "sdw-last-updated"):
        with open(Notify.LAST_UPDATED_FILE, "w") as f:
            # With apologies to HAL 9000
            f.write("daisy, daisy, give me your answer do")
        warning_should_be_shown = Notify.is_update_check_necessary()
        assert warning_should_be_shown is True
        mocked_error.assert_called_once()
        error_string = mocked_error.call_args[0][0]
        assert re.search(BAD_TIMESTAMP_REGEX, error_string) is not None


def test_uptime_is_sane():
    """
    Even in a CI container this should be greater than zero :-)
    """
    seconds = Notify.get_uptime_seconds()
    assert isinstance(seconds, float)
    assert seconds > 0
