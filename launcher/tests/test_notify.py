import datetime
import re
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from sdw_notify import Notify
from sdw_updater import Updater
from sdw_util import Util
from securedrop_manage.products import Product

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

# Regex for lock conflicts
BUSY_LOCK_REGEX = r"Error obtaining lock on '.*'."

CONFLICTING_PROCESS_REGEX = r"Conflicting process .* is currently running."

# Fixtures (sample files) for certain tests
FIXTURES_PATH = Path(__file__).parent / "fixtures"

DEBIAN_VERSION = 13


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


@mock.patch("sdw_notify.Notify.sdlog.error")
@mock.patch("sdw_notify.Notify.sdlog.warning")
@mock.patch("sdw_notify.Notify.sdlog.info")
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
            can_get_lock = Notify.can_obtain_lock(basename)
            mocked_lockf.assert_called_once()
            assert can_get_lock is False
            error_string = mocked_error.call_args[0][0]
            assert re.search(BUSY_LOCK_REGEX, error_string) is not None


@mock.patch("sdw_notify.Notify.sdlog.error")
@mock.patch("sdw_notify.Notify.sdlog.warning")
@mock.patch("sdw_notify.Notify.sdlog.info")
def test_no_lockfile_no_problems(mocked_info, mocked_warning, mocked_error, tmp_path):
    """
    Test whether our shared lock test succeeds even when there's no lockfile
    (which means the process has not run recently, or ever, and it's safe to
    run the potentially conflicting process).
    """
    with mock.patch("sdw_util.Util.LOCK_DIRECTORY", tmp_path):
        lock_result = Notify.can_obtain_lock("404.lock")
        assert lock_result is True


@mock.patch("sdw_notify.Notify.sdlog.error")
@mock.patch("sdw_notify.Notify.sdlog.warning")
@mock.patch("sdw_notify.Notify.sdlog.info")
def test_stale_lockfile_has_no_effect(mocked_info, mocked_warning, mocked_error, tmp_path):
    """
    Test whether we can get a shared lock when a lockfile exists, but nobody
    is accessing it.
    """
    with mock.patch("sdw_util.Util.LOCK_DIRECTORY", tmp_path):
        # Because we're not assigning the return value, it will be immediately released
        basename = "test-stale.lock"
        Util.obtain_lock(basename)
        lock_result = Notify.can_obtain_lock(basename)
        assert lock_result is True


@pytest.mark.parametrize(("return_code", "expected_result"), [(0, True), (1, False)])
@mock.patch("sdw_notify.Notify.sdlog.error")
@mock.patch("sdw_notify.Notify.sdlog.warning")
@mock.patch("sdw_notify.Notify.sdlog.info")
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
        running_process = Notify.is_conflicting_process_running(["cowsay"])
        mocked_run.assert_called_once()
        if expected_result is True:
            assert running_process is True
            mocked_error.assert_called_once()
            error_string = mocked_error.call_args[0][0]
            assert re.search(CONFLICTING_PROCESS_REGEX, error_string) is not None
        else:
            assert running_process is False
            assert not mocked_error.called


def qvm_ls_output(vm: str, state: str) -> bytes:
    return (
        "NAME     STATE     CLASS     LABEL     TEMPLATE\n"
        f"{vm}    {state}    AppVM   yellow     {vm}-debian-{DEBIAN_VERSION}\n"
    ).encode()


@pytest.mark.parametrize(
    ("product", "states", "expected"),
    [
        (Product.JOURNALIST, {"sd-app": "Halted"}, True),
        (Product.JOURNALIST, {"sd-app": "Running"}, False),
        (Product.JOURNALIST, {"sd-app": "Paused"}, False),
        (Product.ADMIN, {"sd-admin": "Halted"}, True),
        (Product.ADMIN, {"sd-admin": "Running"}, False),
        (Product.ALL, {"sd-app": "Halted", "sd-admin": "Halted"}, True),
        (Product.ALL, {"sd-app": "Running", "sd-admin": "Halted"}, False),
        (Product.ALL, {"sd-app": "Halted", "sd-admin": "Running"}, False),
    ],
)
@mock.patch("sdw_util.Util.OS_RELEASE_FILE", FIXTURES_PATH / "os-release-qubes-4.1")
def test_are_session_vms_halted(product, states, expected):
    """
    When the VMs for the installed product(s) are all halted
    Then `Notify.are_session_vms_halted()` should return True
    When any of them is in another state
    Then it should return False
     And only the VMs for the installed product(s) should be checked
    """
    with (
        mock.patch("sdw_notify.Notify.get_installed_product", return_value=product),
        mock.patch(
            "subprocess.check_output", side_effect=lambda cmd: qvm_ls_output(cmd[1], states[cmd[1]])
        ) as mocked_output,
    ):
        assert Notify.are_session_vms_halted() is expected
    checked = [c.args[0][1] for c in mocked_output.call_args_list]
    assert set(checked) <= set(states)
    if expected:
        assert checked == list(states)


@mock.patch("sdw_util.Util.OS_RELEASE_FILE", FIXTURES_PATH / "os-release-qubes-4.1")
@mock.patch("sdw_notify.Notify.get_installed_product", return_value=Product.ALL)
@mock.patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "check_output"))
def test_are_session_vms_halted_error(patched_subprocess, patched_product):
    """
    When the VM status check encounters an error
    Then the call to Notify.are_session_vms_halted() should still complete
     And the method should return False
    """
    assert not Notify.are_session_vms_halted()


@mock.patch("sdw_util.Util.OS_RELEASE_FILE", FIXTURES_PATH / "os-release-ubuntu")
@mock.patch("subprocess.check_output")
def test_are_session_vms_halted_not_qubes(patched_subprocess):
    """
    When not running on Qubes
    Then Notify.are_session_vms_halted() should return False without running qvm-ls
    """
    assert not Notify.are_session_vms_halted()
    assert not patched_subprocess.called
