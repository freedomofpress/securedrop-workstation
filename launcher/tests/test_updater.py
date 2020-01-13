import imp
import os
import pytest
import subprocess
from datetime import datetime
from unittest import mock
from unittest.mock import call

relpath_updater_script = "../sdw_updater_gui/Updater.py"
path_to_script = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), relpath_updater_script
)
updater = imp.load_source("Updater", path_to_script)
from Updater import UpdateStatus  # noqa: E402
from Updater import current_templates  # noqa: E402

debian_based_vms = [
    "sd-svs",
    "sd-log",
    "sd-svs-disp",
    "sd-gpg",
    "sd-proxy",
    "sd-whonix",
    "sd-export",
]

TEST_RESULTS_1 = {
    "dom0": UpdateStatus.UPDATES_OK,
    "fedora": UpdateStatus.UPDATES_OK,
    "sd-svs": UpdateStatus.UPDATES_OK,
    "sd-svs-disp": UpdateStatus.UPDATES_OK,
}

TEST_RESULTS_2 = {
    "dom0": UpdateStatus.UPDATES_OK,
    "fedora": UpdateStatus.UPDATES_FAILED,
    "sd-svs": UpdateStatus.UPDATES_OK,
    "sd-svs-disp": UpdateStatus.UPDATES_OK,
}

TEST_RESULTS_3 = {
    "dom0": UpdateStatus.UPDATES_OK,
    "fedora": UpdateStatus.REBOOT_REQUIRED,
    "sd-svs": UpdateStatus.UPDATES_OK,
    "sd-svs-disp": UpdateStatus.UPDATES_OK,
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
    status = updater._check_updates_debian("sd-svs")
    assert status == UpdateStatus.UPDATES_OK
    info_log = [
        call("Checking for updates {}:{}".format("sd-svs", "sd-svs-buster-template")),
        call("{} is up to date".format("sd-svs-buster-template")),
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
    status = updater._check_updates_debian("sd-svs")
    assert status == UpdateStatus.UPDATES_REQUIRED
    error_log = [
        call(
            "Updates required for {} or cannot check for updates".format(
                "sd-svs-buster-template"
            )
        ),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    info_log = [
        call("Checking for updates {}:{}".format("sd-svs", "sd-svs-buster-template")),
    ]
    mocked_error.assert_has_calls(error_log)
    mocked_info.assert_has_calls(info_log)


@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_debian_updates_failed(mocked_info, mocked_error, mocked_call, capsys):
    status = updater._check_updates_debian("sd-svs")
    assert status == UpdateStatus.UPDATES_FAILED
    error_log = [
        call(
            "Updates required for {} or cannot check for updates".format(
                "sd-svs-buster-template"
            )
        ),
        call("Command 'check_call' returned non-zero exit status 1."),
        call("Failed to shut down {}".format("sd-svs-buster-template")),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    info_log = [
        call("Checking for updates {}:{}".format("sd-svs", "sd-svs-buster-template")),
    ]
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
        call(["qvm-shutdown", current_templates["fedora"]]),
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
            call(["qvm-shutdown", current_templates[vm]]),
        ]
    elif vm == "fedora":
        subprocess_call_list = [
            call(["qvm-run", current_templates[vm], "dnf check-update"]),
            call(["qvm-shutdown", current_templates[vm]]),
        ]
    elif vm == "dom0":
        subprocess_call_list = [
            call(["sudo", "qubes-dom0-update", "--check-only"]),
        ]
    else:
        pytest.fail("Unupported VM: {}".format(vm))
    mocked_call.assert_has_calls(subprocess_call_list)
    assert not mocked_error.called


@mock.patch("Updater.check_updates", return_value=0)
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_all_updates(
    mocked_info, mocked_error, mocked_call, mocked_check_updates
):
    updater.check_all_updates()
    check_updates_call_list = [call(x) for x in current_templates.keys()]
    mocked_check_updates.assert_has_calls(check_updates_call_list)
    mocked_subprocess_calls = [
        call(
            [
                "qvm-run",
                "sd-svs",
                "echo '0' > {}".format(updater.FLAG_FILE_STATUS_SD_SVS),
            ]
        ),
        call(
            [
                "qvm-run",
                "sd-svs",
                "echo '{}' > /home/user/sdw-last-updated".format(
                    str(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
                ),
            ]
        ),
    ]
    mocked_call.assert_has_calls(mocked_subprocess_calls)
    assert not mocked_error.called


@pytest.mark.parametrize("status", UpdateStatus)
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_write_updates_status_flag_sd_svs(
    mocked_info, mocked_error, mocked_call, status
):
    updater._write_updates_status_flag_sd_svs(status)
    mocked_call.assert_called_once_with(
        [
            "qvm-run",
            "sd-svs",
            "echo '{}' > {}".format(status.value, updater.FLAG_FILE_STATUS_SD_SVS),
        ]
    )
    assert not mocked_error.called


@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_write_last_updated_flags_to_disk(mocked_info, mocked_error, mocked_call):
    updater._write_last_updated_flags_to_disk()
    current_time_utc = str(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    subprocess_command = [
        "qvm-run",
        "sd-svs",
        "echo '{}' > {}".format(
            current_time_utc, updater.FLAG_FILE_LAST_UPDATED_SD_SVS
        ),
    ]
    mocked_call.assert_called_once_with(subprocess_command)
    assert os.path.exists(updater.FLAG_FILE_LAST_UPDATED_DOM0)
    try:
        contents = open(updater.FLAG_FILE_LAST_UPDATED_DOM0, "r").read()
        assert contents == current_time_utc
    except Exception:
        pytest.fail("Error reading file")


@mock.patch("subprocess.check_call", side_effect="0")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_dom0_success(mocked_info, mocked_error, mocked_call):
    result = updater._apply_updates_dom0()
    assert result == UpdateStatus.REBOOT_REQUIRED
    mocked_call.assert_called_once_with(["sudo", "qubes-dom0-update", "-y"])
    assert not mocked_error.called


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


def test_overall_update_status_1():
    result = updater.overall_update_status(TEST_RESULTS_1)
    assert result == UpdateStatus.UPDATES_OK


def test_overall_update_status_2():
    result = updater.overall_update_status(TEST_RESULTS_2)
    assert result == UpdateStatus.UPDATES_FAILED


def test_overall_update_status_3():
    result = updater.overall_update_status(TEST_RESULTS_3)
    assert result == UpdateStatus.REBOOT_REQUIRED
