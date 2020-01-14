#!/usr/bin/env python3
"""
Utility library for checking and applying SecureDrop Workstation VM updates.

This library is meant to be called by the SecureDrop launcher, which
is opened by the user when clicking on the desktop, opening sdw-laucher.py
from the parent directory.
"""

import logging
import os
import subprocess
from datetime import datetime
from enum import Enum

FLAG_FILE_STATUS_SD_SVS = "sdw-update-flag"
FLAG_FILE_LAST_UPDATED_SD_SVS = "sdw-last-updated"
FLAG_FILE_STATUS_DOM0 = ".securedrop_launcher/sdw-update-flag"
FLAG_FILE_LAST_UPDATED_DOM0 = ".securedrop_launcher/sdw-last-updated"

sdlog = logging.getLogger(__name__)

# The are the TemplateVMs that require full patch level at boot in order to start the client,
# as well as their associated TemplateVMs.
# In the future, we could use qvm-prefs to extract this information.
current_templates = {
    "dom0": "dom0",
    "fedora": "fedora-30",
    "sd-svs-disp": "sd-svs-disp-buster-template",
    "sd-svs": "sd-svs-buster-template",
    "sd-log": "sd-log-buster-template",
    "sd-export": "sd-export-buster-template",
    "sd-proxy": "sd-proxy-buster-template",
    "sd-whonix": "whonix-gw-15",
    "sd-gpg": "securedrop-workstation-buster",
}


def get_path(folder):
    return os.path.join(os.path.expanduser("~"), folder)


def check_all_updates(progress_callback=None):
    """
    Check for updates for all vms listed in current_templates above
    """

    update_results = {}
    sdlog.info("Checking for all updates")

    progress_current = 0
    progress_total = len(current_templates.keys())

    for vm in current_templates.keys():
        # update the progressBar via callback method
        if progress_callback:
            sdlog.info("Updating {} of {}".format(progress_current + 1, progress_total))
            progress_callback(int((progress_current / progress_total) * 100))
            progress_current += 1
        update_results[vm] = check_updates(vm)

    # write the flags to disk
    overall_status = overall_update_status(update_results)
    _write_updates_status_flag_to_disk(overall_status)
    if overall_status == UpdateStatus.UPDATES_OK:
        _write_last_updated_flags_to_disk()

    return update_results


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


def apply_updates(vms, progress_callback=None):
    """
    Apply updates to the TemplateVMs of VM list specified in parameter
    """
    upgrade_results = {}
    sdlog.info("Applying all updates")

    progress_current = 0
    progress_total = len(vms)

    for vm in vms:
        # update the progressBar via callback method
        if progress_callback:
            sdlog.info(
                "Upgrading {} of {}".format(progress_current + 1, progress_total)
            )
            progress_callback(int((progress_current / progress_total) * 100))
            progress_current += 1
        if vm == "dom0":
            upgrade_results[vm] = _apply_updates_dom0(vm)
        else:
            upgrade_results[vm] = _apply_updates_vm(vm)

    overall_status = overall_update_status(upgrade_results)
    # If we are rebooting anyways, no need to cycle the VMs
    if overall_status != UpdateStatus.REBOOT_REQUIRED:
        _shutdown_and_start_vms()
    # write the flags to disk
    _write_updates_status_flag_to_disk(overall_status)
    if overall_status == UpdateStatus.UPDATES_OK:
        _write_last_updated_flags_to_disk()

    return upgrade_results


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
        try:
            subprocess.check_call(["qvm-shutdown", current_templates["fedora"]])
        except subprocess.CalledProcessError as e:
            sdlog.error("Failed to shut down {}".format(current_templates["fedora"]))
            sdlog.error(str(e))
            return UpdateStatus.UPDATES_FAILED
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
        try:
            subprocess.check_call(["qvm-shutdown", current_templates[vm]])
        except subprocess.CalledProcessError as e:
            sdlog.error("Failed to shut down {}".format(current_templates[vm]))
            sdlog.error(str(e))
            return UpdateStatus.UPDATES_FAILED

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
    Writes the time of last successful upgrade to dom0 and sd-svs
    """
    current_date = str(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    # flag_file_sd_svs_status = get_path(FLAG_FILE_LAST_UPDATED_SD_SVS)
    flag_file_sd_svs_last_updated = get_path(FLAG_FILE_LAST_UPDATED_SD_SVS)
    flag_file_dom0_last_updated = get_path(FLAG_FILE_LAST_UPDATED_DOM0)

    try:
        sdlog.info("Setting last updated to {} in sd-svs".format(current_date))
        subprocess.check_call(
            [
                "qvm-run",
                "sd-svs",
                "echo '{}' > {}".format(current_date, flag_file_sd_svs_last_updated),
            ]
        )
    except subprocess.CalledProcessError as e:
        sdlog.error("Error writing last updated flag to sd-svs")
        sdlog.error(str(e))

    try:
        sdlog.info("Setting last updated to {} in dom0".format(current_date))
        if not os.path.exists(os.path.dirname(flag_file_dom0_last_updated)):
            os.makedirs(os.path.dirname(flag_file_dom0_last_updated))
        f = open(flag_file_dom0_last_updated, "w+")
        f.write(current_date)
        f.close()
    except Exception as e:
        sdlog.error("Error writing last updated flag to dom0")
        sdlog.error(str(e))


def _write_updates_status_flag_to_disk(status):
    """
    Writes the latest SecureDrop Workstation update status to disk, on both
    dom0 and sd-svs for futher processing in the future.
    """
    flag_file_path_sd_svs = get_path(FLAG_FILE_STATUS_SD_SVS)
    flag_file_path_dom0 = get_path(FLAG_FILE_STATUS_DOM0)

    try:
        sdlog.info("Setting update flag to {} in sd-svs".format(status.value))
        subprocess.check_call(
            [
                "qvm-run",
                "sd-svs",
                "echo '{}' > {}".format(status.value, flag_file_path_sd_svs),
            ]
        )
    except subprocess.CalledProcessError as e:
        sdlog.error("Error writing update status flag to sd-svs")
        sdlog.error(str(e))

    try:
        sdlog.info("Setting update flag to {} in dom0".format(status.value))
        if not os.path.exists(os.path.dirname(flag_file_path_dom0)):
            os.makedirs(os.path.dirname(flag_file_path_dom0))
        f = open(flag_file_path_dom0, "w+")
        f.write(status.value)
        f.close()
    except Exception as e:
        sdlog.error("Error writing update status flag to dom0")
        sdlog.error(str(e))


def overall_update_status(results):
    """
    Helper method that returns the worst-case status
    For now, simple logic for reboot required: If dom0 or fedora updates, a
    reboot will be required.
    """
    updates_failed = False
    updates_required = False
    reboot_required = False

    for result in results.values():
        if result == UpdateStatus.UPDATES_FAILED:
            updates_failed = True
        elif result == UpdateStatus.REBOOT_REQUIRED:
            reboot_required = True
        elif result == UpdateStatus.UPDATES_REQUIRED:
            updates_required = True

    if updates_failed:
        return UpdateStatus.UPDATES_FAILED
    if reboot_required:
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
    vms_in_order = ["sd-proxy", "sd-whonix", "sd-svs", "sd-gpg", "sd-log"]

    for vm in vms_in_order:
        _safely_shutdown_vm(vm)

    for vm in vms_in_order:
        _safely_start_vm(vm)


def _safely_shutdown_vm(vm):
    try:
        subprocess.check_call(["qvm-shutdown", "--wait", vm])
    except subprocess.CalledProcessError as e:
        sdlog.error("Error while shutting down {}".format(vm))
        sdlog.error(str(e))


def _safely_start_vm(vm):
    try:
        subprocess.check_call(["qvm-start", vm])
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
