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

DEFAULT_HOME = os.path.join(os.path.expanduser("~"), ".securedrop_launcher")

FLAG_FILE_STATUS_SD_SVS = "/home/user/sdw-update-flag"
FLAG_FILE_LAST_UPDATED_SD_SVS = "/home/user/sdw-last-updated"
FLAG_FILE_LAST_UPDATED_DOM0 = os.path.join(DEFAULT_HOME, "sdw-last-updated")

sdlog = logging.getLogger(__name__)

# The are the TemplateVMs that require full patch level at boot in order to start the client,
# as well as their associated TemplateVMs.
# In the future, we could use qvm-prefs to extract this information.
current_templates = {
    "fedora": "fedora-30",
    "sd-svs-disp": "sd-svs-disp-buster-template",
    "sd-svs": "sd-svs-buster-template",
    "sd-log": "sd-log-buster-template",
    "sd-export": "sd-export-buster-template",
    "sd-proxy": "sd-proxy-buster-template",
    "sd-whonix": "whonix-gw-15",
    "sd-gpg": "securedrop-workstation-buster",
}


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
    _write_updates_status_flag_sd_svs(overall_status)
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

    # write the flags to disk
    overall_status = overall_update_status(upgrade_results)
    _write_updates_status_flag_sd_svs(overall_status)
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

    sdlog.info("{} is up to date".format(current_templates[vm]))
    if not updates_required:
        return UpdateStatus.UPDATES_OK
    else:
        return UpdateStatus.UPDATES_REQUIRED


def _apply_updates_dom0():
    """
    Apply updates to dom0
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
    # TODO: check for xen updates here and return REBOOT_REQUIRED
    sdlog.info("dom0 update successful")
    return UpdateStatus.UPDATES_OK


def _apply_updates_vm(vm):
    """
    Apply updates to a given Debian-based TemplateVM
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
        # subprocess.check_call(["qvm-shutdown", current_templates[vm]])
    except subprocess.CalledProcessError as e:
        sdlog.error(
            "An error has occurred updating {}. Please contact your administrator.".format(
                current_templates[vm]
            )
        )
        sdlog.error(str(e))
        return UpdateStatus.UPDATES_FAILED
    sdlog.info("{} update successful".format(current_templates[vm]))
    return _reboot_appvm_after_update(vm)


def _reboot_appvm_after_update(vm):
    """
    Reboots a given AppVM once its template has been updated. This will ensure the
    changes are applied to this AppVM.
    """
    sdlog.info("Rebooting {} after upgrade of {}".format(vm, current_templates[vm]))

    # Special case, will require a full workstation reboot later
    if vm == "fedora":
        pass
    else:
        try:
            subprocess.check_call(["qvm-shutdown", vm])
            subprocess.check_call(["qvm-start", "--skip-if-running", vm])
            return UpdateStatus.UPDATES_OK
        except subprocess.CalledProcessError as e:
            sdlog.error("Error while rebooting {}".format(vm))
            sdlog.error(str(e))
            return UpdateStatus.UPDATES_FAILED


def _write_last_updated_flags_to_disk():
    """
    Writes the time of last successful upgrade to dom0 and sd-svs
    """
    current_date = str(datetime.utcnow())
    try:
        sdlog.info("Setting last updated to {} in sd-svs".format(current_date))
        subprocess.check_call(
            [
                "qvm-run",
                "sd-svs",
                "echo '{}' > {}".format(current_date, FLAG_FILE_LAST_UPDATED_SD_SVS),
            ]
        )
    except subprocess.CalledProcessError as e:
        sdlog.error("Error writing last updated flag to sd-svs")
        sdlog.error(e)

    try:
        sdlog.info("Setting last updated to {} in dom0".format(current_date))
        f = open(FLAG_FILE_LAST_UPDATED_DOM0, "w")
        f.write(current_date)
        f.close()
    except Exception as e:
        sdlog.error("Error writing last updated flag to dom0")
        sdlog.error(str(e))


def _write_updates_status_flag_sd_svs(status):
    try:
        sdlog.info("Setting update flag to {} in sd-svs".format(status.value))
        subprocess.check_call(
            [
                "qvm-run",
                "sd-svs",
                "echo '{}' > {}".format(status.value, FLAG_FILE_STATUS_SD_SVS),
            ]
        )
    except subprocess.CalledProcessError as e:
        sdlog.error("Error writing update status flag to sd-svs")
        sdlog.error(e)


def overall_update_status(results):
    """
    Helper method that returns the worst-case status
    """
    updates_failed = False
    reboot_required = False
    updates_required = False

    for result in results.values():
        if result == UpdateStatus.UPDATES_FAILED:
            updates_failed = True
        elif result == UpdateStatus.UPDATES_REQUIRED:
            updates_required = True
        elif result == UpdateStatus.REBOOT_REQUIRED:
            reboot_required = True

    if updates_failed:
        return UpdateStatus.UPDATES_FAILED
    elif reboot_required:
        return UpdateStatus.REBOOT_REQUIRED
    elif updates_required:
        return UpdateStatus.UPDATES_REQUIRED
    else:
        return UpdateStatus.UPDATES_OK


class UpdateStatus(Enum):
    """
    Standardizes return codes for update/upgrade methods
    """

    UPDATES_OK = "0"
    UPDATES_REQUIRED = "1"
    REBOOT_REQUIRED = "2"
    UPDATES_FAILED = "3"
