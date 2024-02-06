import json
import os
import pytest
import subprocess
from importlib.machinery import SourceFileLoader
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory
from unittest import mock
from unittest.mock import call

relpath_updater_script = "../sdw_updater_gui/Updater.py"
path_to_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), relpath_updater_script)
updater = SourceFileLoader("Updater", path_to_script).load_module()
from Updater import UpdateStatus  # noqa: E402
from Updater import current_templates  # noqa: E402
from Updater import current_vms  # noqa: E402

temp_dir = TemporaryDirectory().name

debian_based_vms = [
    "sd-app",
    "sd-log",
    "sd-viewer",
    "sd-gpg",
    "sd-proxy",
    "sd-whonix",
    "sd-devices",
]

DEBIAN_VERSION = "bullseye"

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
    assert len(updater.current_vms) == 8


def test_updater_templatevms_present():
    assert len(updater.current_templates) == 4


@mock.patch("Updater._write_updates_status_flag_to_disk")
@mock.patch("Updater._write_last_updated_flags_to_disk")
@mock.patch("Updater._apply_updates_vm")
@mock.patch("Updater._apply_updates_dom0", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("Updater._check_updates_dom0", return_value=UpdateStatus.UPDATES_REQUIRED)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_dom0_updates_available(
    mocked_info, mocked_error, check_dom0, apply_dom0, apply_vm, write_updated, write_status
):
    upgrade_generator = updater.apply_updates(["dom0"])
    results = {}

    for vm, progress, result in upgrade_generator:
        results[vm] = result
        assert progress is not None

    assert updater.overall_update_status(results) == UpdateStatus.UPDATES_OK
    assert not mocked_error.called
    # Ensure we check for updates, and apply them (with no parameters)
    check_dom0.assert_called_once_with()
    apply_dom0.assert_called_once_with()
    assert not apply_vm.called


@mock.patch("Updater._write_updates_status_flag_to_disk")
@mock.patch("Updater._write_last_updated_flags_to_disk")
@mock.patch("Updater._apply_updates_vm")
@mock.patch("Updater._apply_updates_dom0")
@mock.patch("Updater._check_updates_dom0", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_dom0_no_updates(
    mocked_info, mocked_error, check_dom0, apply_dom0, apply_vm, write_updated, write_status
):
    upgrade_generator = updater.apply_updates(["dom0"])
    results = {}

    for vm, progress, result in upgrade_generator:
        results[vm] = result
        assert progress is not None

    assert updater.overall_update_status(results) == UpdateStatus.UPDATES_OK
    assert not mocked_error.called
    # We check for updates, but do not attempt to apply them
    check_dom0.assert_called_once_with()
    assert not apply_dom0.called
    assert not apply_vm.called


@mock.patch("Updater._write_updates_status_flag_to_disk")
@mock.patch("Updater._write_last_updated_flags_to_disk")
@mock.patch(
    "Updater._apply_updates_vm",
    side_effect=[UpdateStatus.UPDATES_OK, UpdateStatus.UPDATES_REQUIRED],
)
@mock.patch("Updater._apply_updates_dom0")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_required(
    mocked_info, mocked_error, apply_dom0, apply_vm, write_updated, write_status
):
    upgrade_generator = updater.apply_updates(["fedora", "sd-app"])
    results = {}

    for vm, progress, result in upgrade_generator:
        results[vm] = result
        assert progress is not None

    assert results == {"fedora": UpdateStatus.UPDATES_OK, "sd-app": UpdateStatus.UPDATES_REQUIRED}
    calls = [call("fedora"), call("sd-app")]
    apply_vm.assert_has_calls(calls)

    assert results == {"fedora": UpdateStatus.UPDATES_OK, "sd-app": UpdateStatus.UPDATES_REQUIRED}

    assert updater.overall_update_status(results) == UpdateStatus.UPDATES_REQUIRED
    assert not mocked_error.called
    assert not apply_dom0.called


@pytest.mark.parametrize("status", UpdateStatus)
@mock.patch("os.path.expanduser", return_value=temp_dir)
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_write_updates_status_flag_to_disk(
    mocked_info, mocked_error, mocked_call, mocked_expand, status
):
    flag_file_sd_app = updater.FLAG_FILE_STATUS_SD_APP
    flag_file_dom0 = updater.get_dom0_path(updater.FLAG_FILE_STATUS_DOM0)

    updater._write_updates_status_flag_to_disk(status)

    mocked_call.assert_called_once_with(
        ["qvm-run", "sd-app", "echo '{}' > {}".format(status.value, flag_file_sd_app)]
    )

    assert os.path.exists(flag_file_dom0)
    try:
        with open(flag_file_dom0, "r") as f:
            contents = json.load(f)
            assert contents["status"] == status.value
    except Exception:
        pytest.fail("Error reading file")
    assert "tmp" in flag_file_dom0
    assert not mocked_error.called


@pytest.mark.parametrize("status", UpdateStatus)
@mock.patch("os.path.expanduser", return_value=temp_dir)
@mock.patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call"))
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_write_updates_status_flag_to_disk_failure_app(
    mocked_info, mocked_error, mocked_call, mocked_expand, status
):

    error_calls = [
        call("Error writing update status flag to sd-app"),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    updater._write_updates_status_flag_to_disk(status)
    mocked_error.assert_has_calls(error_calls)


@pytest.mark.parametrize("status", UpdateStatus)
@mock.patch("os.path.exists", side_effect=OSError("os_error"))
@mock.patch("os.path.expanduser", return_value=temp_dir)
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_write_updates_status_flag_to_disk_failure_dom0(
    mocked_info, mocked_error, mocked_call, mocked_expand, mocked_open, status
):

    error_calls = [call("Error writing update status flag to dom0"), call("os_error")]
    updater._write_updates_status_flag_to_disk(status)
    mocked_error.assert_has_calls(error_calls)


@mock.patch("os.path.expanduser", return_value=temp_dir)
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_write_last_updated_flags_to_disk(mocked_info, mocked_error, mocked_call, mocked_expand):
    flag_file_sd_app = updater.FLAG_FILE_LAST_UPDATED_SD_APP
    flag_file_dom0 = updater.get_dom0_path(updater.FLAG_FILE_LAST_UPDATED_DOM0)
    current_time = str(datetime.now().strftime(updater.DATE_FORMAT))

    updater._write_last_updated_flags_to_disk()
    subprocess_command = [
        "qvm-run",
        "sd-app",
        "echo '{}' > {}".format(current_time, flag_file_sd_app),
    ]
    mocked_call.assert_called_once_with(subprocess_command)
    assert not mocked_error.called
    assert os.path.exists(flag_file_dom0)
    try:
        contents = open(flag_file_dom0, "r").read()
        assert contents == current_time
    except Exception:
        pytest.fail("Error reading file")


@mock.patch("os.path.expanduser", return_value=temp_dir)
@mock.patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call"))
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_write_last_updated_flags_to_disk_fails(
    mocked_info, mocked_error, mocked_call, mocked_expand
):
    error_log = [
        call("Error writing last updated flag to sd-app"),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    updater._write_last_updated_flags_to_disk()

    mocked_error.assert_has_calls(error_log)


@mock.patch("os.path.exists", return_value=False)
@mock.patch("os.path.expanduser", return_value=temp_dir)
@mock.patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call"))
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_write_last_updated_flags_dom0_folder_creation_fail(
    mocked_info, mocked_error, mocked_call, mocked_expand, mocked_path_exists
):
    error_log = [
        call("Error writing last updated flag to sd-app"),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    updater._write_last_updated_flags_to_disk()

    mocked_error.assert_has_calls(error_log)


@mock.patch("subprocess.check_call")
@mock.patch("Updater._write_updates_status_flag_to_disk")
@mock.patch("Updater._write_last_updated_flags_to_disk")
@mock.patch("Updater.shutdown_and_start_vms")
@mock.patch("Updater._check_updates_dom0", return_value=UpdateStatus.UPDATES_REQUIRED)
@mock.patch("Updater._apply_updates_vm")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_dom0_updates_applied(
    mocked_info,
    mocked_error,
    apply_vm,
    check_dom0,
    shutdown,
    write_updated,
    write_status,
    mocked_call,
):
    result = updater._apply_updates_dom0()
    assert result == UpdateStatus.REBOOT_REQUIRED
    mocked_call.assert_called_once_with(["sudo", "qubes-dom0-update", "-y"])
    assert not mocked_error.called
    assert not apply_vm.called


@mock.patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call"))
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_dom0_failure(mocked_info, mocked_error, mocked_call):
    result = updater._apply_updates_dom0()
    error_log = [
        call("An error has occurred updating dom0. Please contact your administrator."),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]

    assert mocked_call.called
    assert result == UpdateStatus.UPDATES_FAILED
    mocked_error.assert_has_calls(error_log)


@pytest.mark.parametrize("vm", current_templates)
@mock.patch("subprocess.check_call", side_effect="0")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_vms(mocked_info, mocked_error, mocked_call, vm):
    if vm != "dom0":
        result = updater._apply_updates_vm(vm)
        assert result == UpdateStatus.UPDATES_OK

        if vm.startswith("fedora") or vm.startswith("whonix"):
            expected_salt_state = "update.qubes-vm"
        else:
            expected_salt_state = "fpf-apt-repo"

        mocked_call.assert_called_once_with(
            ["sudo", "qubesctl", "--skip-dom0", "--targets", vm, "state.sls", expected_salt_state]
        )
        assert not mocked_error.called


@pytest.mark.parametrize("vm", current_templates)
@mock.patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call"))
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_vms_fails(mocked_info, mocked_error, mocked_call, vm):
    error_calls = [
        call("An error has occurred updating {}. Please contact your administrator.".format(vm)),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    result = updater._apply_updates_vm(vm)
    assert result == UpdateStatus.UPDATES_FAILED

    mocked_error.assert_has_calls(error_calls)


@mock.patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call"))
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_dom0_updates_available(mocked_info, mocked_error, mocked_call):
    result = updater._check_updates_dom0()

    error_calls = [
        call("dom0 updates required, or cannot check for updates"),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    mocked_error.assert_has_calls(error_calls)
    assert result == UpdateStatus.UPDATES_REQUIRED


@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_dom0_no_updates_available(mocked_info, mocked_error, mocked_call):
    result = updater._check_updates_dom0()
    assert not mocked_error.called
    mocked_info.assert_called_once_with("No updates available for dom0")
    assert result == UpdateStatus.UPDATES_OK


@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_overall_update_status_results_updates_ok(mocked_info, mocked_error):
    result = updater.overall_update_status(TEST_RESULTS_OK)
    assert result == UpdateStatus.UPDATES_OK
    assert not mocked_error.called


@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_overall_update_status_updates_failed(mocked_info, mocked_error):
    result = updater.overall_update_status(TEST_RESULTS_FAILED)
    assert result == UpdateStatus.UPDATES_FAILED
    assert not mocked_error.called


@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_overall_update_status_reboot_required(mocked_info, mocked_error):
    result = updater.overall_update_status(TEST_RESULTS_REBOOT)
    assert result == UpdateStatus.REBOOT_REQUIRED
    assert not mocked_error.called


@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_overall_update_status_updates_required(mocked_info, mocked_error):
    result = updater.overall_update_status(TEST_RESULTS_UPDATES)
    assert result == UpdateStatus.UPDATES_REQUIRED
    assert not mocked_error.called


@mock.patch("Updater.last_required_reboot_performed", return_value=True)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_overall_update_status_reboot_was_done_previously(
    mocked_info, mocked_error, mocked_reboot_performed
):
    result = updater.overall_update_status(TEST_RESULTS_UPDATES)
    assert result == UpdateStatus.UPDATES_REQUIRED
    assert not mocked_error.called


@mock.patch("Updater.last_required_reboot_performed", return_value=False)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_overall_update_status_reboot_not_done_previously(
    mocked_info, mocked_error, mocked_reboot_performed
):
    result = updater.overall_update_status(TEST_RESULTS_UPDATES)
    assert result == UpdateStatus.REBOOT_REQUIRED
    assert not mocked_error.called


@pytest.mark.parametrize("vm", current_vms.keys())
@mock.patch("subprocess.check_output")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_safely_shutdown(mocked_info, mocked_error, mocked_output, vm):
    call_list = [call(["qvm-shutdown", "--wait", "{}".format(vm)], stderr=-1)]

    updater._safely_shutdown_vm(vm)
    mocked_output.assert_has_calls(call_list)
    assert not mocked_error.called


@pytest.mark.parametrize("vm", current_vms.keys())
@mock.patch("subprocess.check_output", side_effect=["0", "0", "0"])
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_safely_start(mocked_info, mocked_error, mocked_output, vm):
    call_list = [
        call(["qvm-ls", "--running", "--raw-list"], stderr=-1),
        call(["qvm-start", "--skip-if-running", vm], stderr=-1),
    ]

    updater._safely_start_vm(vm)
    mocked_output.assert_has_calls(call_list)
    assert not mocked_error.called


@pytest.mark.parametrize("vm", current_vms.keys())
@mock.patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "check_output"))
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_safely_start_fails(mocked_info, mocked_error, mocked_output, vm):
    call_list = [
        call("Error while starting {}".format(vm)),
        call("Command 'check_output' returned non-zero exit status 1."),
    ]

    updater._safely_start_vm(vm)
    mocked_error.assert_has_calls(call_list)


@pytest.mark.parametrize("vm", current_vms.keys())
@mock.patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "check_output"))
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_safely_shutdown_fails(mocked_info, mocked_error, mocked_call, vm):
    call_list = [
        call("Failed to shut down {}".format(vm)),
        call("Command 'check_output' returned non-zero exit status 1."),
    ]

    updater._safely_shutdown_vm(vm)
    mocked_error.assert_has_calls(call_list)


@mock.patch("subprocess.check_output")
@mock.patch("Updater._safely_start_vm")
@mock.patch("Updater._safely_shutdown_vm")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_shutdown_and_start_vms(
    mocked_info, mocked_error, mocked_shutdown, mocked_start, mocked_output
):
    sys_vm_kill_calls = [
        call(["qvm-kill", "sys-firewall"], stderr=-1),
        call(["qvm-kill", "sys-net"], stderr=-1),
    ]
    sys_vm_shutdown_calls = [call("sys-usb"), call("sys-whonix")]
    sys_vm_start_calls = [
        call("sys-net"),
        call("sys-firewall"),
        call("sys-whonix"),
        call("sys-usb"),
    ]
    template_vm_calls = [
        call("fedora-38"),
        call("sd-large-{}-template".format(DEBIAN_VERSION)),
        call("sd-small-{}-template".format(DEBIAN_VERSION)),
        call("whonix-gateway-17"),
    ]
    app_vm_calls = [
        call("sd-app"),
        call("sd-proxy"),
        call("sd-whonix"),
        call("sd-gpg"),
        call("sd-log"),
    ]
    updater.shutdown_and_start_vms()
    mocked_output.assert_has_calls(sys_vm_kill_calls)
    mocked_shutdown.assert_has_calls(template_vm_calls + app_vm_calls + sys_vm_shutdown_calls)
    app_vm_calls_reversed = list(reversed(app_vm_calls))
    mocked_start.assert_has_calls(sys_vm_start_calls + app_vm_calls_reversed)
    assert not mocked_error.called


@mock.patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "check_output"))
@mock.patch("Updater._safely_start_vm")
@mock.patch("Updater._safely_shutdown_vm")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_shutdown_and_start_vms_sysvm_fail(
    mocked_info, mocked_error, mocked_shutdown, mocked_start, mocked_output
):
    sys_vm_kill_calls = [
        call(["qvm-kill", "sys-firewall"], stderr=-1),
        call(["qvm-kill", "sys-net"], stderr=-1),
    ]
    sys_vm_start_calls = [
        call("sys-net"),
        call("sys-firewall"),
        call("sys-whonix"),
        call("sys-usb"),
    ]
    app_vm_calls = [
        call("sd-app"),
        call("sd-proxy"),
        call("sd-whonix"),
        call("sd-gpg"),
        call("sd-log"),
    ]
    template_vm_calls = [
        call("fedora-38"),
        call("sd-large-{}-template".format(DEBIAN_VERSION)),
        call("sd-small-{}-template".format(DEBIAN_VERSION)),
        call("whonix-gateway-17"),
    ]
    error_calls = [
        call("Error while killing system VM: sys-firewall"),
        call("Command 'check_output' returned non-zero exit status 1."),
        call("None"),
        call("Error while killing system VM: sys-net"),
        call("Command 'check_output' returned non-zero exit status 1."),
        call("None"),
    ]
    updater.shutdown_and_start_vms()
    mocked_output.assert_has_calls(sys_vm_kill_calls)
    mocked_shutdown.assert_has_calls(template_vm_calls + app_vm_calls)
    app_vm_calls_reversed = list(reversed(app_vm_calls))
    mocked_start.assert_has_calls(sys_vm_start_calls + app_vm_calls_reversed)
    mocked_error.assert_has_calls(error_calls)


@pytest.mark.parametrize("status", UpdateStatus)
@mock.patch("subprocess.check_call")
@mock.patch("os.path.expanduser", return_value=temp_dir)
@mock.patch("Updater.sdlog.error")
def test_read_dom0_update_flag_from_disk(
    mocked_error, mocked_expanduser, mocked_subprocess, status
):
    updater._write_updates_status_flag_to_disk(status)

    flag_file_dom0 = updater.get_dom0_path(updater.FLAG_FILE_STATUS_DOM0)

    assert os.path.exists(flag_file_dom0)
    try:
        with open(flag_file_dom0, "r") as f:
            contents = json.load(f)
            assert contents["status"] == status.value
    except Exception:
        pytest.fail("Error reading file")
    assert "tmp" in flag_file_dom0

    assert updater.read_dom0_update_flag_from_disk() == status
    json_values = updater.read_dom0_update_flag_from_disk(with_timestamp=True)
    assert json_values["status"] == status.value

    assert not mocked_error.called


@mock.patch("subprocess.check_call")
@mock.patch("os.path.expanduser", return_value=temp_dir)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_read_dom0_update_flag_from_disk_fails(
    mocked_info, mocked_error, mocked_expanduser, mocked_subprocess
):

    flag_file_dom0 = updater.get_dom0_path(updater.FLAG_FILE_STATUS_DOM0)
    try:
        with open(flag_file_dom0, "w") as f:
            f.write("something")
    except Exception:
        pytest.fail("Error writing file")

    info_calls = [call("Cannot read dom0 status flag, assuming first run")]

    assert updater.read_dom0_update_flag_from_disk() is None
    assert not mocked_error.called
    mocked_info.assert_has_calls(info_calls)


@mock.patch(
    "Updater.read_dom0_update_flag_from_disk",
    return_value={
        "last_status_update": "1999-09-09 14:12:12",
        "status": UpdateStatus.REBOOT_REQUIRED.value,
    },
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_last_required_reboot_performed_successful(mocked_info, mocked_error, mocked_read):
    result = updater.last_required_reboot_performed()
    assert result is True
    assert not mocked_error.called


@mock.patch(
    "Updater.read_dom0_update_flag_from_disk",
    return_value={
        "last_status_update": str(datetime.now().strftime(updater.DATE_FORMAT)),
        "status": UpdateStatus.REBOOT_REQUIRED.value,
    },
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_last_required_reboot_performed_failed(mocked_info, mocked_error, mocked_read):
    result = updater.last_required_reboot_performed()
    assert result is False
    assert not mocked_error.called


@mock.patch("Updater.read_dom0_update_flag_from_disk", return_value=None)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_last_required_reboot_performed_no_file(mocked_info, mocked_error, mocked_read):
    result = updater.last_required_reboot_performed()
    assert result is True
    assert not mocked_error.called


@mock.patch(
    "Updater.read_dom0_update_flag_from_disk",
    return_value={
        "last_status_update": str(datetime.now().strftime(updater.DATE_FORMAT)),
        "status": UpdateStatus.UPDATES_OK.value,
    },
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_last_required_reboot_performed_not_required(mocked_info, mocked_error, mocked_read):
    result = updater.last_required_reboot_performed()
    assert result is True
    assert not mocked_error.called


@pytest.mark.parametrize(
    "status, rebooted, expect_status_change, expect_updater",
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
@mock.patch("Updater._write_updates_status_flag_to_disk")
def test_should_run_updater_status_interval_expired(
    mocked_write, status, rebooted, expect_status_change, expect_updater
):
    TEST_INTERVAL = 3600
    # the updater should always run when checking interval has expired,
    # regardless of update or reboot status
    with mock.patch("Updater.last_required_reboot_performed") as mocked_last:
        mocked_last.return_value = rebooted
        with mock.patch("Updater.read_dom0_update_flag_from_disk") as mocked_read:
            mocked_read.return_value = {
                "last_status_update": str(
                    (datetime.now() - timedelta(seconds=(TEST_INTERVAL + 10))).strftime(
                        updater.DATE_FORMAT
                    )
                ),
                "status": status.value,
            }
            # assuming that the tests won't take an hour to run!
            assert expect_updater == updater.should_launch_updater(TEST_INTERVAL)
            assert expect_status_change == mocked_write.called


@pytest.mark.parametrize(
    "status, rebooted, expect_status_change, expect_updater",
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
@mock.patch("Updater._write_updates_status_flag_to_disk")
def test_should_run_updater_status_interval_not_expired(
    mocked_write, status, rebooted, expect_status_change, expect_updater
):
    TEST_INTERVAL = 3600
    # Even if the interval hasn't expired, the updater should only be skipped when:
    # - the updater status is UPDATESr_OK, or
    # - the updater status is REBOOT_REQUIRED and the reboot has been performed.
    with mock.patch("Updater.last_required_reboot_performed") as mocked_last:
        mocked_last.return_value = rebooted
        with mock.patch("Updater.read_dom0_update_flag_from_disk") as mocked_read:
            mocked_read.return_value = {
                "last_status_update": str(datetime.now().strftime(updater.DATE_FORMAT)),
                "status": status.value,
            }
            # assuming that the tests won't take an hour to run!
            assert expect_updater == updater.should_launch_updater(TEST_INTERVAL)
            assert expect_status_change == mocked_write.called


@mock.patch("Updater._write_updates_status_flag_to_disk")
def test_should_run_updater_invalid_status(mocked_write):
    TEST_INTERVAL = 3600
    with mock.patch("Updater.last_required_reboot_performed") as mocked_last:
        mocked_last.return_value = True
        with mock.patch("Updater.read_dom0_update_flag_from_disk") as mocked_read:
            mocked_read.return_value = {}
            # assuming that the tests won't take an hour to run!
            assert updater.should_launch_updater(TEST_INTERVAL) is True


@mock.patch("Updater._write_updates_status_flag_to_disk")
def test_should_run_updater_invalid_timestamp(mocked_write):
    TEST_INTERVAL = 3600
    with mock.patch("Updater.last_required_reboot_performed") as mocked_last:
        mocked_last.return_value = True
        with mock.patch("Updater.read_dom0_update_flag_from_disk") as mocked_read:
            mocked_read.return_value = {
                "last_status_update": "time to die",
                "status": UpdateStatus.UPDATES_OK.value,
            }
            # assuming that the tests won't take an hour to run!
            assert updater.should_launch_updater(TEST_INTERVAL) is True


@mock.patch("Updater._write_updates_status_flag_to_disk")
def test_should_run_updater_invalid_status_value(mocked_write):
    TEST_INTERVAL = 3600
    with mock.patch("Updater.last_required_reboot_performed") as mocked_last:
        mocked_last.return_value = True
        with mock.patch("Updater.read_dom0_update_flag_from_disk") as mocked_read:
            mocked_read.return_value = {
                "last_status_update": str(datetime.now().strftime(updater.DATE_FORMAT)),
                "status": "5",
            }
            # assuming that the tests won't take an hour to run!
            assert updater.should_launch_updater(TEST_INTERVAL) is True


@mock.patch("subprocess.check_output", side_effect=[b""])
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_dom0_state_success(mocked_info, mocked_error, mocked_subprocess):
    updater.apply_dom0_state()
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
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_dom0_state_failure(mocked_info, mocked_error, mocked_subprocess):
    updater.apply_dom0_state()
    log_error_calls = [
        call("Failed to apply dom0 state. See launcher-detail.log for details."),
        call("Command 'check_output' returned non-zero exit status 1."),
    ]
    mocked_subprocess.assert_called_once_with(
        ["sudo", "qubesctl", "--show-output", "state.highstate"]
    )
    mocked_info.assert_called_once_with("Applying dom0 state")
    mocked_error.assert_has_calls(log_error_calls)


@mock.patch("os.path.exists", return_value=True)
@mock.patch("os.listdir", return_value=["apple", "banana"])
@mock.patch("Updater.sdlog.info")
def test_migration_is_required(mocked_info, mocked_listdir, mocked_exists):
    assert updater.migration_is_required() is True
    assert mocked_info.called_once_with(
        "Migration is required, will enforce full config during update"
    )


@mock.patch("os.path.exists", return_value=False)
@mock.patch("os.listdir", return_value=[])
@mock.patch("Updater.sdlog.info")
def test_migration_not_required(mocked_info, mocked_listdir, mocked_exists):
    assert updater.migration_is_required() is False
    assert not mocked_info.called


@mock.patch("Updater.sdlog.info")
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
    MIGRATION_DIR = "/tmp/potato"  # nosec
    with mock.patch("Updater.MIGRATION_DIR", MIGRATION_DIR):
        result = updater.run_full_install()
    check_outputs = [call(["sdw-admin", "--apply"])]
    check_calls = [call(["sudo", "rm", "-rf", MIGRATION_DIR])]
    assert mocked_output.call_count == 1
    assert mocked_call.call_count == 1
    assert result == UpdateStatus.UPDATES_OK
    mocked_output.assert_has_calls(check_outputs, any_order=False)
    mocked_call.assert_has_calls(check_calls, any_order=False)


@mock.patch("Updater.sdlog.error")
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
    MIGRATION_DIR = "/tmp/potato"  # nosec
    with mock.patch("Updater.MIGRATION_DIR", MIGRATION_DIR):
        result = updater.run_full_install()
    calls = [call(["sdw-admin", "--apply"])]
    assert mocked_output.call_count == 1
    assert mocked_call.call_count == 0
    assert mocked_error.called
    assert result == UpdateStatus.UPDATES_FAILED
    mocked_output.assert_has_calls(calls, any_order=False)


@mock.patch("Updater.sdlog.error")
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
    MIGRATION_DIR = "/tmp/potato"  # nosec
    with mock.patch("Updater.MIGRATION_DIR", MIGRATION_DIR):
        result = updater.run_full_install()
    check_outputs = [call(["sdw-admin", "--apply"])]
    check_calls = [call(["sudo", "rm", "-rf", MIGRATION_DIR])]
    assert mocked_output.call_count == 1
    assert mocked_call.call_count == 1
    assert mocked_error.called
    assert result == UpdateStatus.UPDATES_FAILED
    mocked_output.assert_has_calls(check_outputs, any_order=False)
    mocked_call.assert_has_calls(check_calls, any_order=False)
