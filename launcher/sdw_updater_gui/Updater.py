#!/usr/bin/env python3
"""
Utility library for checking and applying SecureDrop Workstation VM updates.

This library is meant to be called by the SecureDrop launcher, which
is opened by the user when clicking on the desktop, opening sdw-laucher.py
from the parent directory.
"""

import json
import logging
import os
import subprocess
from datetime import datetime, timedelta
from enum import Enum

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
FLAG_FILE_STATUS_SD_APP = "/home/user/.securedrop_client/sdw-update-status"
FLAG_FILE_LAST_UPDATED_SD_APP = "/home/user/.securedrop_client/sdw-last-updated"
FLAG_FILE_STATUS_DOM0 = ".securedrop_launcher/sdw-update-status"
FLAG_FILE_LAST_UPDATED_DOM0 = ".securedrop_launcher/sdw-last-updated"

sdlog = logging.getLogger(__name__)

# The are the TemplateVMs that require full patch level at boot in order to start the client,
# as well as their associated TemplateVMs.
# In the future, we could use qvm-prefs to extract this information.
current_templates = {
    "dom0": "dom0",
    "fedora": "fedora-30",
    "sd-viewer": "sd-viewer-buster-template",
    "sd-app": "sd-app-buster-template",
    "sd-log": "sd-log-buster-template",
    "sd-devices": "sd-devices-buster-template",
    "sd-proxy": "sd-proxy-buster-template",
    "sd-whonix": "whonix-gw-15",
    "sd-gpg": "securedrop-workstation-buster",
}


def get_dom0_path(folder):
    return os.path.join(os.path.expanduser("~"), folder)


def check_all_updates():
    """
    Check for updates for all vms listed in current_templates above
    """

    sdlog.info("Checking for all updates")

    for progress_current, vm in enumerate(current_templates.keys()):
        # yield the progress percentage for UI updates
        progress_percentage = int(
            ((progress_current + 1) / len(current_templates.keys())) * 100
        )
        update_results = check_updates(vm)
        yield vm, progress_percentage, update_results


def check_updates(vm):
    """
    Check for updates for a single VM
    """
    if vm == "dom0":
        return _check_updates_dom0()
    elif vm == "fedora":
        return _check_updates_fedora()
    else:
        return _check_updates_debian(vm)


def apply_updates(vms):
    """
    Apply updates to the TemplateVMs of VM list specified in parameter
    """
    sdlog.info("Applying all updates")

    for progress_current, vm in enumerate(vms):
        upgrade_results = UpdateStatus.UPDATES_FAILED

        if vm == "dom0":
            upgrade_results = _apply_updates_dom0()
        else:
            upgrade_results = _apply_updates_vm(vm)

        progress_percentage = int(((progress_current + 1) / len(vms)) * 100 - 5)
        yield vm, progress_percentage, upgrade_results

    _shutdown_and_start_vms()


def _check_updates_dom0():
    """
    Check for dom0 updates
    """
    try:
        subprocess.check_call(["sudo", "qubes-dom0-update", "--check-only"])
    except subprocess.CalledProcessError as e:
        sdlog.error("dom0 updates required or cannot check for updates")
        sdlog.error(str(e))
        return UpdateStatus.UPDATES_REQUIRED

    sdlog.info("dom0 is up to date")
    return UpdateStatus.UPDATES_OK


def _check_updates_fedora():
    """
    Check for updates to the default Fedora TemplateVM
    """
    try:
        subprocess.check_call(
            ["qvm-run", current_templates["fedora"], "dnf check-update"]
        )
    except subprocess.CalledProcessError as e:
        sdlog.error(
            "Updates required for {} or cannot check for updates".format(
                current_templates["fedora"]
            )
        )
        sdlog.error(str(e))
        return UpdateStatus.UPDATES_REQUIRED
    finally:
        reboot_status = _safely_shutdown_vm(current_templates["fedora"])
        if reboot_status == UpdateStatus.UPDATES_FAILED:
            return reboot_status

    sdlog.info("{} is up to date".format(current_templates["fedora"]))
    return UpdateStatus.UPDATES_OK


def _check_updates_debian(vm):
    """
    Check for updates for a given Debian-based TemplateVM
    """
    updates_required = False
    try:
        # There is no apt command that uses exit codes in such a way that we can discover if
        # updates are required by relying on exit codes.
        # Since we don't want to use --pass-io and parse the output, we have to count
        # the lines on the vm output
        sdlog.info("Checking for updates {}:{}".format(vm, current_templates[vm]))
        subprocess.check_call(["qvm-run", current_templates[vm], "sudo apt update"])
        subprocess.check_call(
            [
                "qvm-run",
                current_templates[vm],
                "[[ $(apt list --upgradable | wc -l) -eq 1 ]]",
            ]
        )
    except subprocess.CalledProcessError as e:
        sdlog.error(
            "Updates required for {} or cannot check for updates".format(
                current_templates[vm]
            )
        )
        sdlog.error(str(e))
        updates_required = True
    finally:
        reboot_status = _safely_shutdown_vm(current_templates[vm])
        if reboot_status == UpdateStatus.UPDATES_FAILED:
            return reboot_status

    if not updates_required:
        sdlog.info("{} is up to date".format(current_templates[vm]))
        return UpdateStatus.UPDATES_OK
    else:
        return UpdateStatus.UPDATES_REQUIRED


def _apply_updates_dom0():
    """
    Apply updates to dom0. Any update to dom0 will require a reboot after
    the upgrade.
    """
    sdlog.info("Updating dom0")
    try:
        subprocess.check_call(["sudo", "qubes-dom0-update", "-y"])
    except subprocess.CalledProcessError as e:
        sdlog.error(
            "An error has occurred updating dom0. Please contact your administrator."
        )
        sdlog.error(str(e))
        return UpdateStatus.UPDATES_FAILED
    sdlog.info("dom0 update successful")
    return UpdateStatus.REBOOT_REQUIRED


def _apply_updates_vm(vm):
    """
    Apply updates to a given TemplateVM. Any update to the base fedora template
    will require a reboot after the upgrade.
    """
    sdlog.info("Updating {}:{}".format(vm, current_templates[vm]))
    try:
        subprocess.check_call(
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
    except subprocess.CalledProcessError as e:
        sdlog.error(
            "An error has occurred updating {}. Please contact your administrator.".format(
                current_templates[vm]
            )
        )
        sdlog.error(str(e))
        return UpdateStatus.UPDATES_FAILED
    sdlog.info("{} update successful".format(current_templates[vm]))
    if vm == "fedora":
        return UpdateStatus.REBOOT_REQUIRED
    else:
        return UpdateStatus.UPDATES_OK


def _write_last_updated_flags_to_disk():
    """
    Writes the time of last successful upgrade to dom0 and sd-app
    """
    current_date = str(datetime.now().strftime(DATE_FORMAT))

    flag_file_sd_app_last_updated = FLAG_FILE_LAST_UPDATED_SD_APP
    flag_file_dom0_last_updated = get_dom0_path(FLAG_FILE_LAST_UPDATED_DOM0)

    try:
        sdlog.info("Setting last updated to {} in sd-app".format(current_date))
        subprocess.check_call(
            [
                "qvm-run",
                "sd-app",
                "echo '{}' > {}".format(current_date, flag_file_sd_app_last_updated),
            ]
        )
    except subprocess.CalledProcessError as e:
        sdlog.error("Error writing last updated flag to sd-app")
        sdlog.error(str(e))

    try:
        sdlog.info("Setting last updated to {} in dom0".format(current_date))
        if not os.path.exists(os.path.dirname(flag_file_dom0_last_updated)):
            os.makedirs(os.path.dirname(flag_file_dom0_last_updated))
        with open(flag_file_dom0_last_updated, "w") as f:
            f.write(current_date)
    except Exception as e:
        sdlog.error("Error writing last updated flag to dom0")
        sdlog.error(str(e))


def _write_updates_status_flag_to_disk(status):
    """
    Writes the latest SecureDrop Workstation update status to disk, on both
    dom0 and sd-app for futher processing in the future.
    """
    flag_file_path_sd_app = FLAG_FILE_STATUS_SD_APP
    flag_file_path_dom0 = get_dom0_path(FLAG_FILE_STATUS_DOM0)

    try:
        sdlog.info("Setting update flag to {} in sd-app".format(status.value))
        subprocess.check_call(
            [
                "qvm-run",
                "sd-app",
                "echo '{}' > {}".format(status.value, flag_file_path_sd_app),
            ]
        )
    except subprocess.CalledProcessError as e:
        sdlog.error("Error writing update status flag to sd-app")
        sdlog.error(str(e))

    try:
        sdlog.info("Setting update flag to {} in dom0".format(status.value))
        if not os.path.exists(os.path.dirname(flag_file_path_dom0)):
            os.makedirs(os.path.dirname(flag_file_path_dom0))

        current_date = str(datetime.now().strftime(DATE_FORMAT))

        with open(flag_file_path_dom0, "w") as f:
            flag_contents = {"last_status_update": current_date, "status": status.value}
            json.dump(flag_contents, f)
    except Exception as e:
        sdlog.error("Error writing update status flag to dom0")
        sdlog.error(str(e))


def last_required_reboot_performed():
    """
        Checks if the dom0 flag file indicates that a reboot is required, and
        if so, will check current uptime with the data at which the reboot
        was requested. This will be used by the _write_updates_status_flag_to_disk
        function to preserve the status UPDATES_REQUIRED instead of updating.
        """
    flag_contents = read_dom0_update_flag_from_disk(with_timestamp=True)

    # No flag exists on disk (yet)
    if flag_contents is None:
        return True

    if int(flag_contents["status"]) == int(UpdateStatus.REBOOT_REQUIRED.value):
        reboot_time = datetime.strptime(
            flag_contents["last_status_update"], DATE_FORMAT
        )
        boot_time = datetime.now() - _get_uptime()

        # The session was started *before* the reboot was requested by
        # the launcher, system was not rebooted after previous run
        if boot_time < reboot_time:
            return False
        # system was rebooted after flag was written to disk
        else:
            return True
    # previous run did not require reboot
    else:
        return True


def _get_uptime():
    """
    Returns timedelta containing system (dom0) uptime.
    """
    uptime = None
    with open("/proc/uptime", "r") as f:
        uptime = f.read().split(" ")[0].strip()
    uptime = int(float(uptime))
    uptime_hours = uptime // 3600
    uptime_minutes = (uptime % 3600) // 60
    uptime_seconds = uptime % 60

    delta = timedelta(
        hours=uptime_hours, minutes=uptime_minutes, seconds=uptime_seconds
    )

    return delta


def read_dom0_update_flag_from_disk(with_timestamp=False):
    """
    Read the last updated SecureDrop Workstation update status from disk
    in dom0, and returns the corresponding UpdateStatus. If ivoked the
    parameter `with_timestamp=True`, this function will return the full json.
    """
    flag_file_path_dom0 = get_dom0_path(FLAG_FILE_STATUS_DOM0)

    try:
        with open(flag_file_path_dom0, "r") as f:
            contents = json.load(f)
            for status in UpdateStatus:
                if int(contents["status"]) == int(status.value):
                    if with_timestamp:
                        return contents
                    else:
                        return status
    except Exception:
        sdlog.info("Cannot read dom0 status flag, assuming first run")
        return None


def overall_update_status(results):
    """
    Helper method that returns the worst-case status
    For now, simple logic for reboot required: If dom0 or fedora updates, a
    reboot will be required.
    """
    updates_failed = False
    updates_required = False
    reboot_required = False

    # Ensure the user has rebooted after the previous installer run required a reboot
    if not last_required_reboot_performed():
        return UpdateStatus.REBOOT_REQUIRED

    for result in results.values():
        if result == UpdateStatus.UPDATES_FAILED:
            updates_failed = True
        elif result == UpdateStatus.REBOOT_REQUIRED:
            reboot_required = True
        elif result == UpdateStatus.UPDATES_REQUIRED:
            updates_required = True

    if updates_failed:
        return UpdateStatus.UPDATES_FAILED
    elif reboot_required:
        return UpdateStatus.REBOOT_REQUIRED
    elif updates_required:
        return UpdateStatus.UPDATES_REQUIRED
    else:
        return UpdateStatus.UPDATES_OK


def _shutdown_and_start_vms():
    """
    Power cycles the vms to ensure. we should do them all in one shot to reduce complexity
    and likelihood of failure. Rebooting the VMs will ensure the TemplateVM
    updates are picked up by the AppVM. We must first shut all VMs down to ensure
    correct order of operations, as sd-whonix cannot shutdown if sd-proxy is powered
    on, for example.
    """
    vms_in_order = ["sd-proxy", "sd-whonix", "sd-app", "sd-gpg", "sd-log"]
    sdlog.info("Rebooting all vms for updates")
    for vm in vms_in_order:
        _safely_shutdown_vm(vm)

    for vm in vms_in_order:
        _safely_start_vm(vm)


def _safely_shutdown_vm(vm):
    try:
        subprocess.check_call(["qvm-shutdown", "--wait", vm])
    except subprocess.CalledProcessError as e:
        sdlog.error("Failed to shut down {}".format(vm))
        sdlog.error(str(e))
        return UpdateStatus.UPDATES_FAILED


def _safely_start_vm(vm):
    try:
        subprocess.check_call(["qvm-start", "--skip-if-running", vm])
    except subprocess.CalledProcessError as e:
        sdlog.error("Error while starting {}".format(vm))
        sdlog.error(str(e))


class UpdateStatus(Enum):
    """
    Standardizes return codes for update/upgrade methods
    """

    UPDATES_OK = "0"
    UPDATES_REQUIRED = "1"
    REBOOT_REQUIRED = "2"
    UPDATES_FAILED = "3"
