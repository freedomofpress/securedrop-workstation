import json
import os
import pytest
import subprocess
from datetime import datetime
from importlib.machinery import SourceFileLoader
from tempfile import TemporaryDirectory
from unittest import mock
from unittest.mock import call

relpath_updater_script = "../sdw_updater_gui/Updater.py"
path_to_script = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), relpath_updater_script
)
updater = SourceFileLoader("Updater", path_to_script).load_module()
from Updater import UpdateStatus  # noqa: E402
from Updater import current_templates  # noqa: E402

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
    assert len(updater.current_templates) == 9


@mock.patch("subprocess.check_call", return_value=0)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_fedora_up_to_date(
    mocked_info, mocked_error, mocked_call, capsys
):
    status = updater._check_updates_fedora()
    assert status == UpdateStatus.UPDATES_OK
    mocked_info.assert_called_once_with(
        "{} is up to date".format(current_templates["fedora"])
    )
    assert not mocked_error.called


@mock.patch(
    "subprocess.check_call",
    side_effect=[subprocess.CalledProcessError(1, "check_call"), "0"],
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_fedora_needs_updates(
    mocked_info, mocked_error, mocked_call, capsys
):
    status = updater._check_updates_fedora()
    assert status == UpdateStatus.UPDATES_REQUIRED

    error_log = [
        call(
            "Updates required for {} or cannot check for updates".format(
                current_templates["fedora"]
            )
        ),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    mocked_error.assert_has_calls(error_log)
    assert not mocked_info.called


@mock.patch(
    "subprocess.check_call",
    side_effect=[
        subprocess.CalledProcessError(1, "check_call"),
        subprocess.CalledProcessError(1, "check_call"),
    ],
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_fedora_updates_failed(
    mocked_info, mocked_error, mocked_call, capsys
):
    status = updater._check_updates_fedora()
    assert status == UpdateStatus.UPDATES_FAILED
    error_log = [
        call(
            "Updates required for {} or cannot check for updates".format(
                current_templates["fedora"]
            )
        ),
        call("Command 'check_call' returned non-zero exit status 1."),
        call("Failed to shut down {}".format(current_templates["fedora"])),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    mocked_error.assert_has_calls(error_log)
    assert not mocked_info.called


@mock.patch("subprocess.check_call", return_value=0)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_dom0_up_to_date(mocked_info, mocked_error, mocked_call, capsys):
    status = updater._check_updates_dom0()
    assert status == UpdateStatus.UPDATES_OK
    mocked_info.assert_called_once_with("dom0 is up to date")
    assert not mocked_error.called


@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_dom0_needs_updates(
    mocked_info, mocked_error, mocked_call, capsys
):
    status = updater._check_updates_dom0()
    assert status == UpdateStatus.UPDATES_REQUIRED
    error_log = [
        call("dom0 updates required or cannot check for updates"),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    mocked_error.assert_has_calls(error_log)
    assert not mocked_info.called


@mock.patch("subprocess.check_call", return_value=0)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_debian_updates_up_to_date(
    mocked_info, mocked_error, mocked_call, capsys
):
    status = updater._check_updates_debian("sd-app")
    assert status == UpdateStatus.UPDATES_OK
    info_log = [
        call("Checking for updates {}:{}".format("sd-app", "sd-app-buster-template")),
        call("{} is up to date".format("sd-app-buster-template")),
    ]
    mocked_info.assert_has_calls(info_log)
    assert not mocked_error.called


@mock.patch(
    "subprocess.check_call",
    side_effect=[subprocess.CalledProcessError(1, "check_call"), "0"],
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_debian_updates_required(
    mocked_info, mocked_error, mocked_call, capsys
):
    status = updater._check_updates_debian("sd-app")
    assert status == UpdateStatus.UPDATES_REQUIRED
    error_log = [
        call(
            "Updates required for {} or cannot check for updates".format(
                "sd-app-buster-template"
            )
        ),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    info_log = [
        call("Checking for updates {}:{}".format("sd-app", "sd-app-buster-template")),
    ]
    mocked_error.assert_has_calls(error_log)
    mocked_info.assert_has_calls(info_log)


@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_debian_updates_failed(mocked_info, mocked_error, mocked_call, capsys):
    status = updater._check_updates_debian("sd-app")
    assert status == UpdateStatus.UPDATES_FAILED
    error_log = [
        call(
            "Updates required for {} or cannot check for updates".format(
                "sd-app-buster-template"
            )
        ),
        call("Command 'check_call' returned non-zero exit status 1."),
        call("Failed to shut down {}".format("sd-app-buster-template")),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    info_log = [
        call("Checking for updates {}:{}".format("sd-app", "sd-app-buster-template")),
    ]
    mocked_error.assert_has_calls(error_log)
    mocked_info.assert_has_calls(info_log)


@mock.patch(
    "subprocess.check_call",
    side_effect=[subprocess.CalledProcessError(1, "check_call"), "0", "0"],
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_debian_has_updates(mocked_info, mocked_error, mocked_call, capsys):
    error_log = [
        call(
            "Updates required for {} or cannot check for updates".format(
                "sd-log-buster-template"
            )
        ),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    info_log = [
        call("Checking for updates {}:{}".format("sd-log", "sd-log-buster-template")),
    ]

    status = updater._check_updates_debian("sd-log")
    assert status == UpdateStatus.UPDATES_REQUIRED

    mocked_error.assert_has_calls(error_log)
    mocked_info.assert_has_calls(info_log)


@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_fedora_calls_fedora(mocked_info, mocked_error, mocked_call):
    status = updater.check_updates("fedora")
    assert status == UpdateStatus.UPDATES_OK
    subprocess_call_list = [
        call(["qvm-run", current_templates["fedora"], "dnf check-update"]),
        call(["qvm-shutdown", "--wait", current_templates["fedora"]]),
    ]

    mocked_call.assert_has_calls(subprocess_call_list)


@pytest.mark.parametrize("vm", current_templates.keys())
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_calls_correct_commands(
    mocked_info, mocked_error, mocked_call, vm
):
    status = updater.check_updates(vm)
    assert status == UpdateStatus.UPDATES_OK
    if vm in debian_based_vms:
        subprocess_call_list = [
            call(["qvm-run", current_templates[vm], "sudo apt update"]),
            call(
                [
                    "qvm-run",
                    current_templates[vm],
                    "[[ $(apt list --upgradable | wc -l) -eq 1 ]]",
                ]
            ),
            call(["qvm-shutdown", "--wait", current_templates[vm]]),
        ]
    elif vm == "fedora":
        subprocess_call_list = [
            call(["qvm-run", current_templates[vm], "dnf check-update"]),
            call(["qvm-shutdown", "--wait", current_templates[vm]]),
        ]
    elif vm == "dom0":
        subprocess_call_list = [
            call(["sudo", "qubes-dom0-update", "--check-only"]),
        ]
    else:
        pytest.fail("Unupported VM: {}".format(vm))
    mocked_call.assert_has_calls(subprocess_call_list)
    assert not mocked_error.called


@mock.patch("Updater.check_updates", return_value={"test": UpdateStatus.UPDATES_OK})
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_all_updates(
    mocked_info, mocked_error, mocked_call, mocked_check_updates
):

    update_generator = updater.check_all_updates()
    results = {}

    for vm, progress, result in update_generator:
        results[vm] = result
        assert progress is not None
        results[vm] = result

    check_updates_call_list = [call(x) for x in current_templates.keys()]
    mocked_check_updates.assert_has_calls(check_updates_call_list)

    assert not mocked_call.called
    assert not mocked_error.called
    assert updater.overall_update_status(results) == UpdateStatus.UPDATES_OK


@mock.patch("Updater._write_updates_status_flag_to_disk")
@mock.patch("Updater._write_last_updated_flags_to_disk")
@mock.patch("Updater._shutdown_and_start_vms")
@mock.patch("Updater._apply_updates_vm")
@mock.patch("Updater._apply_updates_dom0", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates(
    mocked_info,
    mocked_error,
    apply_dom0,
    apply_vm,
    shutdown,
    write_updated,
    write_status,
):
    upgrade_generator = updater.apply_updates(["dom0"])
    results = {}

    for vm, progress, result in upgrade_generator:
        results[vm] = result
        assert progress is not None

    assert updater.overall_update_status(results) == UpdateStatus.UPDATES_OK
    assert not mocked_error.called
    # Ensure _apply_updates_dom0 is not called with a parameter
    apply_dom0.assert_called_once_with()
    assert not apply_vm.called


@mock.patch("Updater._write_updates_status_flag_to_disk")
@mock.patch("Updater._write_last_updated_flags_to_disk")
@mock.patch("Updater._shutdown_and_start_vms")
@mock.patch(
    "Updater._apply_updates_vm",
    side_effect=[UpdateStatus.UPDATES_OK, UpdateStatus.UPDATES_REQUIRED],
)
@mock.patch("Updater._apply_updates_dom0")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_required(
    mocked_info,
    mocked_error,
    apply_dom0,
    apply_vm,
    shutdown,
    write_updated,
    write_status,
):
    upgrade_generator = updater.apply_updates(["fedora", "sd-app"])
    results = {}

    for vm, progress, result in upgrade_generator:
        results[vm] = result
        assert progress is not None

    assert results == {
        "fedora": UpdateStatus.UPDATES_OK,
        "sd-app": UpdateStatus.UPDATES_REQUIRED,
    }
    calls = [call("fedora"), call("sd-app")]
    apply_vm.assert_has_calls(calls)

    assert results == {
        "fedora": UpdateStatus.UPDATES_OK,
        "sd-app": UpdateStatus.UPDATES_REQUIRED,
    }

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
@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
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

    error_calls = [
        call("Error writing update status flag to dom0"),
        call("os_error"),
    ]
    updater._write_updates_status_flag_to_disk(status)
    mocked_error.assert_has_calls(error_calls)


@mock.patch("os.path.expanduser", return_value=temp_dir)
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_write_last_updated_flags_to_disk(
    mocked_info, mocked_error, mocked_call, mocked_expand
):
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
@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
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
@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
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
@mock.patch("Updater._shutdown_and_start_vms")
@mock.patch("Updater._apply_updates_vm")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_dom0_success(
    mocked_info,
    mocked_error,
    apply_vm,
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


@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_dom0_failure(mocked_info, mocked_error, mocked_call):
    result = updater._apply_updates_dom0()
    error_log = [
        call("An error has occurred updating dom0. Please contact your administrator."),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    assert result == UpdateStatus.UPDATES_FAILED
    mocked_error.assert_has_calls(error_log)


@pytest.mark.parametrize("vm", current_templates.keys())
@mock.patch("subprocess.check_call", side_effect="0")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_vms(mocked_info, mocked_error, mocked_call, vm):
    if vm != "dom0":
        result = updater._apply_updates_vm(vm)
        if vm in ["fedora"]:
            assert result == UpdateStatus.REBOOT_REQUIRED
        else:
            assert result == UpdateStatus.UPDATES_OK

        mocked_call.assert_called_once_with(
            [
                "sudo",
                "qubesctl",
                "--skip-dom0",
                "--targets",
                current_templates[vm],
                "state.sls",
                "update.qubes-vm",
            ]
        )
        assert not mocked_error.called


@pytest.mark.parametrize("vm", current_templates.keys())
@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_vms_fails(mocked_info, mocked_error, mocked_call, vm):
    error_calls = [
        call(
            "An error has occurred updating {}. Please contact your administrator.".format(
                current_templates[vm]
            )
        ),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    result = updater._apply_updates_vm(vm)
    assert result == UpdateStatus.UPDATES_FAILED

    mocked_error.assert_has_calls(error_calls)


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


@pytest.mark.parametrize("vm", current_templates.keys())
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_safely_shutdown(mocked_info, mocked_error, mocked_call, vm):
    call_list = [
        call(["qvm-shutdown", "--wait", "{}".format(vm)]),
    ]

    updater._safely_shutdown_vm(vm)
    mocked_call.assert_has_calls(call_list)
    assert not mocked_error.called


@pytest.mark.parametrize("vm", current_templates.keys())
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_safely_start(mocked_info, mocked_error, mocked_call, vm):
    call_list = [
        call(["qvm-start", "--skip-if-running", "{}".format(vm)]),
    ]

    updater._safely_start_vm(vm)
    mocked_call.assert_has_calls(call_list)
    assert not mocked_error.called


@pytest.mark.parametrize("vm", current_templates.keys())
@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_safely_start_fails(mocked_info, mocked_error, mocked_call, vm):
    call_list = [
        call("Error while starting {}".format(vm)),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]

    updater._safely_start_vm(vm)
    mocked_error.assert_has_calls(call_list)


@pytest.mark.parametrize("vm", current_templates.keys())
@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_safely_shutdown_fails(mocked_info, mocked_error, mocked_call, vm):
    call_list = [
        call("Failed to shut down {}".format(vm)),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]

    updater._safely_shutdown_vm(vm)
    mocked_error.assert_has_calls(call_list)


@mock.patch("Updater._safely_start_vm")
@mock.patch("Updater._safely_shutdown_vm")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_shutdown_and_start_vms(
    mocked_info, mocked_error, mocked_shutdown, mocked_start
):
    call_list = [
        call("sd-proxy"),
        call("sd-whonix"),
        call("sd-app"),
        call("sd-gpg"),
    ]
    updater._shutdown_and_start_vms()
    mocked_shutdown.assert_has_calls(call_list)
    mocked_start.assert_has_calls(call_list)
    assert not mocked_error.called


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

    info_calls = [
        call("Cannot read dom0 status flag, assuming first run"),
    ]

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
def test_last_required_reboot_performed_successful(
    mocked_info, mocked_error, mocked_read
):
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


@mock.patch(
    "Updater.read_dom0_update_flag_from_disk",
    return_value={
        "last_status_update": str(datetime.now().strftime(updater.DATE_FORMAT)),
        "status": UpdateStatus.UPDATES_OK.value,
    },
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_last_required_reboot_performed_not_required(
    mocked_info, mocked_error, mocked_read
):
    result = updater.last_required_reboot_performed()
    assert result is True
    assert not mocked_error.called
