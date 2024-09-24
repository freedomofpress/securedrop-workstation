import json
import os
import subprocess
from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import call

import pytest

from sdw_updater import Updater
from sdw_updater.Updater import UpdateStatus

debian_based_vms = [
    "sd-app",
    "sd-log",
    "sd-viewer",
    "sd-gpg",
    "sd-proxy",
    "sd-whonix",
    "sd-devices",
]

DEBIAN_VERSION = "bookworm"

TEST_RESULTS_OK = {
    "dom0": UpdateStatus.UPDATES_OK,
    "fedora": UpdateStatus.UPDATES_OK,
    "sd-app": UpdateStatus.UPDATES_OK,
    "sd-viewer": UpdateStatus.UPDATES_OK,
}

TEST_RESULTS_FAILED = {
    "dom0": UpdateStatus.UPDATES_OK,
    "fedora": UpdateStatus.UPDATES_FAILED,
    "sd-app": UpdateStatus.UPDATES_OK,
    "sd-viewer": UpdateStatus.UPDATES_OK,
}

TEST_RESULTS_REBOOT = {
    "dom0": UpdateStatus.UPDATES_OK,
    "fedora": UpdateStatus.REBOOT_REQUIRED,
    "sd-app": UpdateStatus.UPDATES_OK,
    "sd-viewer": UpdateStatus.UPDATES_OK,
}

TEST_RESULTS_UPDATES = {
    "dom0": UpdateStatus.UPDATES_OK,
    "fedora": UpdateStatus.UPDATES_OK,
    "sd-app": UpdateStatus.UPDATES_OK,
    "sd-viewer": UpdateStatus.UPDATES_REQUIRED,
}


def test_updater_vms_present():
    assert len(Updater.current_vms) == 8


def test_updater_templatevms_present():
    assert len(Updater.current_templates) == 4


@mock.patch("sdw_updater.Updater._write_updates_status_flag_to_disk")
@mock.patch("sdw_updater.Updater._write_last_updated_flags_to_disk")
@mock.patch("sdw_updater.Updater._apply_updates_dom0", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater._check_updates_dom0", return_value=UpdateStatus.UPDATES_REQUIRED)
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_apply_updates_dom0_updates_available(
    mocked_info, mocked_error, check_dom0, apply_dom0, write_updated, write_status
):
    assert Updater.apply_updates_dom0() == UpdateStatus.UPDATES_OK
    assert not mocked_error.called
    # Ensure we check for updates, and apply them (with no parameters)
    check_dom0.assert_called_once_with()
    apply_dom0.assert_called_once_with()


@mock.patch("sdw_updater.Updater._write_updates_status_flag_to_disk")
@mock.patch("sdw_updater.Updater._write_last_updated_flags_to_disk")
@mock.patch("sdw_updater.Updater._apply_updates_dom0")
@mock.patch("sdw_updater.Updater._check_updates_dom0", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_apply_updates_dom0_no_updates(
    mocked_info, mocked_error, check_dom0, apply_dom0, write_updated, write_status
):
    assert Updater.apply_updates_dom0() == UpdateStatus.UPDATES_OK
    assert not mocked_error.called
    # We check for updates, but do not attempt to apply them
    check_dom0.assert_called_once_with()
    assert not apply_dom0.called


@mock.patch("sdw_updater.Updater._write_updates_status_flag_to_disk")
@mock.patch("sdw_updater.Updater._write_last_updated_flags_to_disk")
@mock.patch("sdw_updater.Updater._start_qubes_updater_proc")
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_apply_templates_success(mocked_info, mocked_error, mock_proc, write_updated, write_status):
    result = Updater.apply_updates_templates(templates=[])
    mock_proc.assert_called_once()
    assert result == UpdateStatus.UPDATES_OK
    assert not mocked_error.called


@pytest.mark.parametrize(
    ("templates", "stderr", "expected"),
    [
        (
            ["template"],
            "template updating 0\ntemplate done success",
            UpdateStatus.UPDATES_OK,
        ),
        (
            ["template"],
            "template updating 0\nunknown_keyword",
            UpdateStatus.UPDATES_FAILED,
        ),
        (
            ["tpl1", "tpl2"],
            "tpl1 updating 0\ntpl2 updating 0\tpl1 done success\ntpl2 done error",
            UpdateStatus.UPDATES_FAILED,
        ),
    ],
)
def test_apply_templates(templates, stderr, expected):
    with mock.patch(
        "sdw_updater.Updater._start_qubes_updater_proc",
        return_value=subprocess.Popen(  # noqa: S602
            f"echo '{stderr}' >> /dev/stderr",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ),
    ):
        result = Updater.apply_updates_templates(templates=templates)
        assert result == expected


@pytest.mark.parametrize("status", UpdateStatus)
@mock.patch("subprocess.check_call")
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_write_updates_status_flag_to_disk(
    mocked_info, mocked_error, mocked_call, status, tmp_path
):
    with mock.patch("os.path.expanduser", return_value=tmp_path):
        flag_file_sd_app = Updater.FLAG_FILE_STATUS_SD_APP
        flag_file_dom0 = Updater.get_dom0_path(Updater.FLAG_FILE_STATUS_DOM0)

        Updater._write_updates_status_flag_to_disk(status)

    mocked_call.assert_called_once_with(
        ["qvm-run", "sd-app", f"echo '{status.value}' > {flag_file_sd_app}"]
    )

    assert os.path.exists(flag_file_dom0)
    with open(flag_file_dom0) as f:
        contents = json.load(f)
        assert contents["status"] == status.value
    assert "tmp" in flag_file_dom0
    assert not mocked_error.called


@pytest.mark.parametrize("status", UpdateStatus)
@mock.patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call"))
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_write_updates_status_flag_to_disk_failure_app(
    mocked_info, mocked_error, mocked_call, status, tmp_path
):
    error_calls = [
        call("Error writing update status flag to sd-app"),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    with mock.patch("os.path.expanduser", return_value=tmp_path):
        Updater._write_updates_status_flag_to_disk(status)
    mocked_error.assert_has_calls(error_calls)


@pytest.mark.parametrize("status", UpdateStatus)
@mock.patch("os.path.exists", side_effect=OSError("os_error"))
@mock.patch("subprocess.check_call")
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_write_updates_status_flag_to_disk_failure_dom0(
    mocked_info, mocked_error, mocked_call, mocked_open, status, tmp_path
):
    error_calls = [call("Error writing update status flag to dom0"), call("os_error")]
    with mock.patch("os.path.expanduser", return_value=tmp_path):
        Updater._write_updates_status_flag_to_disk(status)
    mocked_error.assert_has_calls(error_calls)


@mock.patch("subprocess.check_call")
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_write_last_updated_flags_to_disk(mocked_info, mocked_error, mocked_call, tmp_path):
    flag_file_sd_app = Updater.FLAG_FILE_LAST_UPDATED_SD_APP
    with mock.patch("os.path.expanduser", return_value=tmp_path):
        flag_file_dom0 = Updater.get_dom0_path(Updater.FLAG_FILE_LAST_UPDATED_DOM0)
        current_time = str(datetime.now().strftime(Updater.DATE_FORMAT))

        Updater._write_last_updated_flags_to_disk()
    subprocess_command = [
        "qvm-run",
        "sd-app",
        f"echo '{current_time}' > {flag_file_sd_app}",
    ]
    mocked_call.assert_called_once_with(subprocess_command)
    assert not mocked_error.called
    assert os.path.exists(flag_file_dom0)
    with open(flag_file_dom0) as f:
        contents = f.read()

    assert contents == current_time


@mock.patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call"))
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_write_last_updated_flags_to_disk_fails(mocked_info, mocked_error, mocked_call, tmp_path):
    error_log = [
        call("Error writing last updated flag to sd-app"),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    with mock.patch("os.path.expanduser", return_value=tmp_path):
        Updater._write_last_updated_flags_to_disk()
    mocked_error.assert_has_calls(error_log)


@mock.patch("os.path.exists", return_value=False)
@mock.patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call"))
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_write_last_updated_flags_dom0_folder_creation_fail(
    mocked_info, mocked_error, mocked_call, mocked_path_exists, tmp_path
):
    error_log = [
        call("Error writing last updated flag to sd-app"),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    with mock.patch("os.path.expanduser", return_value=tmp_path):
        Updater._write_last_updated_flags_to_disk()
    mocked_error.assert_has_calls(error_log)


@mock.patch("subprocess.check_call")
@mock.patch("sdw_updater.Updater._check_updates_dom0", return_value=UpdateStatus.UPDATES_REQUIRED)
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_apply_updates_dom0_updates_applied(
    mocked_info,
    mocked_error,
    check_dom0,
    mocked_call,
):
    result = Updater._apply_updates_dom0()
    assert result == UpdateStatus.REBOOT_REQUIRED
    mocked_call.assert_called_once_with(["sudo", "qubes-dom0-update", "-y"])
    assert not mocked_error.called


@mock.patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call"))
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_apply_updates_dom0_failure(mocked_info, mocked_error, mocked_call):
    result = Updater._apply_updates_dom0()
    error_log = [
        call("An error has occurred updating dom0. Please contact your administrator."),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]

    assert mocked_call.called
    assert result == UpdateStatus.UPDATES_FAILED
    mocked_error.assert_has_calls(error_log)


@mock.patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call"))
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_check_dom0_updates_available(mocked_info, mocked_error, mocked_call):
    result = Updater._check_updates_dom0()

    error_calls = [
        call("dom0 updates required, or cannot check for updates"),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    mocked_error.assert_has_calls(error_calls)
    assert result == UpdateStatus.UPDATES_REQUIRED


@mock.patch("subprocess.check_call")
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_check_dom0_no_updates_available(mocked_info, mocked_error, mocked_call):
    result = Updater._check_updates_dom0()
    assert not mocked_error.called
    mocked_info.assert_called_once_with("No updates available for dom0")
    assert result == UpdateStatus.UPDATES_OK


@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_overall_update_status_results_updates_ok(mocked_info, mocked_error):
    result = Updater.overall_update_status(TEST_RESULTS_OK)
    assert result == UpdateStatus.UPDATES_OK
    assert not mocked_error.called


@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_overall_update_status_updates_failed(mocked_info, mocked_error):
    result = Updater.overall_update_status(TEST_RESULTS_FAILED)
    assert result == UpdateStatus.UPDATES_FAILED
    assert not mocked_error.called


@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_overall_update_status_reboot_required(mocked_info, mocked_error):
    result = Updater.overall_update_status(TEST_RESULTS_REBOOT)
    assert result == UpdateStatus.REBOOT_REQUIRED
    assert not mocked_error.called


@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_overall_update_status_updates_required(mocked_info, mocked_error):
    result = Updater.overall_update_status(TEST_RESULTS_UPDATES)
    assert result == UpdateStatus.UPDATES_REQUIRED
    assert not mocked_error.called


@mock.patch("sdw_updater.Updater.last_required_reboot_performed", return_value=True)
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_overall_update_status_reboot_was_done_previously(
    mocked_info, mocked_error, mocked_reboot_performed
):
    result = Updater.overall_update_status(TEST_RESULTS_UPDATES)
    assert result == UpdateStatus.UPDATES_REQUIRED
    assert not mocked_error.called


@mock.patch("sdw_updater.Updater.last_required_reboot_performed", return_value=False)
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_overall_update_status_reboot_not_done_previously(
    mocked_info, mocked_error, mocked_reboot_performed
):
    result = Updater.overall_update_status(TEST_RESULTS_UPDATES)
    assert result == UpdateStatus.REBOOT_REQUIRED
    assert not mocked_error.called


@pytest.mark.parametrize("status", UpdateStatus)
@mock.patch("subprocess.check_call")
@mock.patch("sdw_updater.Updater.sdlog.error")
def test_read_dom0_update_flag_from_disk(mocked_error, mocked_subprocess, status, tmp_path):
    with mock.patch("os.path.expanduser", return_value=tmp_path):
        Updater._write_updates_status_flag_to_disk(status)

        flag_file_dom0 = Updater.get_dom0_path(Updater.FLAG_FILE_STATUS_DOM0)

        assert os.path.exists(flag_file_dom0)
        with open(flag_file_dom0) as f:
            contents = json.load(f)
            assert contents["status"] == status.value
        assert "tmp" in flag_file_dom0

        assert Updater.read_dom0_update_flag_from_disk() == status
        json_values = Updater.read_dom0_update_flag_from_disk(with_timestamp=True)
    assert json_values["status"] == status.value

    assert not mocked_error.called


@pytest.mark.parametrize("status", UpdateStatus)
@mock.patch("subprocess.check_call")
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_read_dom0_update_flag_from_disk_fails(
    mocked_info, mocked_error, mocked_subprocess, status, tmp_path
):
    with mock.patch("os.path.expanduser", return_value=tmp_path):
        flag_file_dom0 = Updater.get_dom0_path(Updater.FLAG_FILE_STATUS_DOM0)
    updater_path = tmp_path / ".securedrop_updater"
    updater_path.mkdir()
    with open(flag_file_dom0, "w") as f:
        f.write("something")

    info_calls = [call("Cannot read dom0 status flag, assuming first run")]

    assert Updater.read_dom0_update_flag_from_disk() is None
    assert not mocked_error.called
    mocked_info.assert_has_calls(info_calls)


@mock.patch(
    "sdw_updater.Updater.read_dom0_update_flag_from_disk",
    return_value={
        "last_status_update": "1999-09-09 14:12:12",
        "status": UpdateStatus.REBOOT_REQUIRED.value,
    },
)
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_last_required_reboot_performed_successful(mocked_info, mocked_error, mocked_read):
    result = Updater.last_required_reboot_performed()
    assert result is True
    assert not mocked_error.called


@mock.patch(
    "sdw_updater.Updater.read_dom0_update_flag_from_disk",
    return_value={
        "last_status_update": str(datetime.now().strftime(Updater.DATE_FORMAT)),
        "status": UpdateStatus.REBOOT_REQUIRED.value,
    },
)
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_last_required_reboot_performed_failed(mocked_info, mocked_error, mocked_read):
    result = Updater.last_required_reboot_performed()
    assert result is False
    assert not mocked_error.called


@mock.patch("sdw_updater.Updater.read_dom0_update_flag_from_disk", return_value=None)
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_last_required_reboot_performed_no_file(mocked_info, mocked_error, mocked_read):
    result = Updater.last_required_reboot_performed()
    assert result is True
    assert not mocked_error.called


@mock.patch(
    "sdw_updater.Updater.read_dom0_update_flag_from_disk",
    return_value={
        "last_status_update": str(datetime.now().strftime(Updater.DATE_FORMAT)),
        "status": UpdateStatus.UPDATES_OK.value,
    },
)
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_last_required_reboot_performed_not_required(mocked_info, mocked_error, mocked_read):
    result = Updater.last_required_reboot_performed()
    assert result is True
    assert not mocked_error.called


@pytest.mark.parametrize(
    ("status", "rebooted", "expect_status_change", "expect_updater"),
    [
        (UpdateStatus.UPDATES_OK, True, False, True),
        (UpdateStatus.UPDATES_REQUIRED, True, False, True),
        (UpdateStatus.REBOOT_REQUIRED, True, False, True),
        (UpdateStatus.UPDATES_FAILED, True, False, True),
        (UpdateStatus.UPDATES_OK, False, False, True),
        (UpdateStatus.UPDATES_REQUIRED, False, False, True),
        (UpdateStatus.REBOOT_REQUIRED, False, False, True),
        (UpdateStatus.UPDATES_FAILED, False, False, True),
    ],
)
@mock.patch("sdw_updater.Updater._write_updates_status_flag_to_disk")
def test_should_run_updater_status_interval_expired(
    mocked_write, status, rebooted, expect_status_change, expect_updater
):
    TEST_INTERVAL = 3600
    # the updater should always run when checking interval has expired,
    # regardless of update or reboot status
    with mock.patch("sdw_updater.Updater.last_required_reboot_performed") as mocked_last:
        mocked_last.return_value = rebooted
        with mock.patch("sdw_updater.Updater.read_dom0_update_flag_from_disk") as mocked_read:
            mocked_read.return_value = {
                "last_status_update": str(
                    (datetime.now() - timedelta(seconds=(TEST_INTERVAL + 10))).strftime(
                        Updater.DATE_FORMAT
                    )
                ),
                "status": status.value,
            }
            # assuming that the tests won't take an hour to run!
            assert expect_updater == Updater.should_launch_updater(TEST_INTERVAL)
            assert expect_status_change == mocked_write.called


@pytest.mark.parametrize(
    ("status", "rebooted", "expect_status_change", "expect_updater"),
    [
        (UpdateStatus.UPDATES_OK, True, False, False),
        (UpdateStatus.UPDATES_REQUIRED, True, False, True),
        (UpdateStatus.REBOOT_REQUIRED, True, True, False),
        (UpdateStatus.UPDATES_FAILED, True, False, True),
        (UpdateStatus.UPDATES_OK, False, False, False),
        (UpdateStatus.UPDATES_REQUIRED, False, False, True),
        (UpdateStatus.REBOOT_REQUIRED, False, False, True),
        (UpdateStatus.UPDATES_FAILED, False, False, True),
    ],
)
@mock.patch("sdw_updater.Updater._write_updates_status_flag_to_disk")
def test_should_run_updater_status_interval_not_expired(
    mocked_write, status, rebooted, expect_status_change, expect_updater
):
    TEST_INTERVAL = 3600
    # Even if the interval hasn't expired, the updater should only be skipped when:
    # - the updater status is UPDATESr_OK, or
    # - the updater status is REBOOT_REQUIRED and the reboot has been performed.
    with mock.patch("sdw_updater.Updater.last_required_reboot_performed") as mocked_last:
        mocked_last.return_value = rebooted
        with mock.patch("sdw_updater.Updater.read_dom0_update_flag_from_disk") as mocked_read:
            mocked_read.return_value = {
                "last_status_update": str(datetime.now().strftime(Updater.DATE_FORMAT)),
                "status": status.value,
            }
            # assuming that the tests won't take an hour to run!
            assert expect_updater == Updater.should_launch_updater(TEST_INTERVAL)
            assert expect_status_change == mocked_write.called


@mock.patch("sdw_updater.Updater._write_updates_status_flag_to_disk")
def test_should_run_updater_invalid_status(mocked_write):
    TEST_INTERVAL = 3600
    with mock.patch("sdw_updater.Updater.last_required_reboot_performed") as mocked_last:
        mocked_last.return_value = True
        with mock.patch("sdw_updater.Updater.read_dom0_update_flag_from_disk") as mocked_read:
            mocked_read.return_value = {}
            # assuming that the tests won't take an hour to run!
            assert Updater.should_launch_updater(TEST_INTERVAL) is True


@mock.patch("sdw_updater.Updater._write_updates_status_flag_to_disk")
def test_should_run_updater_invalid_timestamp(mocked_write):
    TEST_INTERVAL = 3600
    with mock.patch("sdw_updater.Updater.last_required_reboot_performed") as mocked_last:
        mocked_last.return_value = True
        with mock.patch("sdw_updater.Updater.read_dom0_update_flag_from_disk") as mocked_read:
            mocked_read.return_value = {
                "last_status_update": "time to die",
                "status": UpdateStatus.UPDATES_OK.value,
            }
            # assuming that the tests won't take an hour to run!
            assert Updater.should_launch_updater(TEST_INTERVAL) is True


@mock.patch("sdw_updater.Updater._write_updates_status_flag_to_disk")
def test_should_run_updater_invalid_status_value(mocked_write):
    TEST_INTERVAL = 3600
    with mock.patch("sdw_updater.Updater.last_required_reboot_performed") as mocked_last:
        mocked_last.return_value = True
        with mock.patch("sdw_updater.Updater.read_dom0_update_flag_from_disk") as mocked_read:
            mocked_read.return_value = {
                "last_status_update": str(datetime.now().strftime(Updater.DATE_FORMAT)),
                "status": "5",
            }
            # assuming that the tests won't take an hour to run!
            assert Updater.should_launch_updater(TEST_INTERVAL) is True


@mock.patch("subprocess.check_output", side_effect=[b""])
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_apply_dom0_state_success(mocked_info, mocked_error, mocked_subprocess):
    Updater.apply_dom0_state()
    log_call_list = [call("Applying dom0 state"), call("Dom0 state applied")]
    mocked_subprocess.assert_called_once_with(
        ["sudo", "qubesctl", "--show-output", "state.highstate"]
    )
    mocked_info.assert_has_calls(log_call_list)
    assert not mocked_error.called


@mock.patch(
    "subprocess.check_output",
    side_effect=[subprocess.CalledProcessError(1, cmd="check_output", output=b"")],
)
@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_apply_dom0_state_failure(mocked_info, mocked_error, mocked_subprocess):
    Updater.apply_dom0_state()
    log_error_calls = [
        call("Failed to apply dom0 state. See updater-detail.log for details."),
        call("Command 'check_output' returned non-zero exit status 1."),
    ]
    mocked_subprocess.assert_called_once_with(
        ["sudo", "qubesctl", "--show-output", "state.highstate"]
    )
    mocked_info.assert_called_once_with("Applying dom0 state")
    mocked_error.assert_has_calls(log_error_calls)


@mock.patch("os.path.exists", return_value=True)
@mock.patch("os.listdir", return_value=["apple", "banana"])
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_migration_is_required(mocked_info, mocked_listdir, mocked_exists):
    assert Updater.migration_is_required() is True
    assert mocked_info.called_once_with(
        "Migration is required, will enforce full config during update"
    )


@mock.patch("os.path.exists", return_value=False)
@mock.patch("os.listdir", return_value=[])
@mock.patch("sdw_updater.Updater.sdlog.info")
def test_migration_not_required(mocked_info, mocked_listdir, mocked_exists):
    assert Updater.migration_is_required() is False
    assert not mocked_info.called


@mock.patch("sdw_updater.Updater.sdlog.info")
@mock.patch("subprocess.check_output", return_value=b"")
@mock.patch("subprocess.check_call")
def test_run_full_install(mocked_call, mocked_output, mocked_info):
    """
    When a full migration is requested
      And the migration succeeds
    Then the migration flag is cleared
      And the success enum is returned
    """
    # subprocess.check_call is mocked, so this directory should never be accessed
    # by the test.
    MIGRATION_DIR = "/tmp/potato"
    with mock.patch("sdw_updater.Updater.MIGRATION_DIR", MIGRATION_DIR):
        result = Updater.run_full_install()
    check_outputs = [call(["sdw-admin", "--apply"])]
    check_calls = [call(["sudo", "rm", "-rf", MIGRATION_DIR])]
    assert mocked_output.call_count == 1
    assert mocked_call.call_count == 1
    assert result == UpdateStatus.UPDATES_OK
    mocked_output.assert_has_calls(check_outputs, any_order=False)
    mocked_call.assert_has_calls(check_calls, any_order=False)


@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch(
    "subprocess.check_output",
    side_effect=[subprocess.CalledProcessError(1, cmd="check_output", output=b"")],
)
@mock.patch("subprocess.check_call", return_value=0)
def test_run_full_install_with_error(mocked_call, mocked_output, mocked_error):
    """
    When a full migration is requested
      And the migration fails in any way
    Then the migration flag is not cleared
      And the error is logged
      And the failure enum is returned
    """
    MIGRATION_DIR = "/tmp/potato"
    with mock.patch("sdw_updater.Updater.MIGRATION_DIR", MIGRATION_DIR):
        result = Updater.run_full_install()
    calls = [call(["sdw-admin", "--apply"])]
    assert mocked_output.call_count == 1
    assert mocked_call.call_count == 0
    assert mocked_error.called
    assert result == UpdateStatus.UPDATES_FAILED
    mocked_output.assert_has_calls(calls, any_order=False)


@mock.patch("sdw_updater.Updater.sdlog.error")
@mock.patch("subprocess.check_output", return_value=b"")
@mock.patch(
    "subprocess.check_call", side_effect=[subprocess.CalledProcessError(1, cmd="check_call")]
)
def test_run_full_install_with_flag_error(mocked_call, mocked_output, mocked_error):
    """
    When a full migration is requested
      And the migration succeeds
      And there is a problem clearing the migration flag
    Then the error is logged
      And the failure enum is returned
    """
    MIGRATION_DIR = "/tmp/potato"
    with mock.patch("sdw_updater.Updater.MIGRATION_DIR", MIGRATION_DIR):
        result = Updater.run_full_install()
    check_outputs = [call(["sdw-admin", "--apply"])]
    check_calls = [call(["sudo", "rm", "-rf", MIGRATION_DIR])]
    assert mocked_output.call_count == 1
    assert mocked_call.call_count == 1
    assert mocked_error.called
    assert result == UpdateStatus.UPDATES_FAILED
    mocked_output.assert_has_calls(check_outputs, any_order=False)
    mocked_call.assert_has_calls(check_calls, any_order=False)
