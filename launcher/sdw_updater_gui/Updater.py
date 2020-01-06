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
from enum import Enum

DEFAULT_HOME = os.path.join(os.path.expanduser("~"), ".securedrop_launcher")
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
    "securedrop-workstation": "securedrop-workstation-buster",
}


def check_all_updates():
    """
    Check for updates for all vms listed in current_templates above
    """

    update_results = {}
    sdlog.info("Checking for all updates")
    for vm in current_templates.keys():
        update_results[vm] = check_updates(vm)

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


def apply_updates(vms):
    """
    Apply updates to the TemplateVMs of VM list specified in parameter
    """
    upgrade_results = {}
    sdlog.info("Applying all updates")

    for vm in vms:
        if vm == "dom0":
            upgrade_results[vm] = _apply_updates_dom0(vm)
        else:
            upgrade_results[vm] = _apply_updates_vm(vm)

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
            subprocess.check_call(
                ["qvm-shutdown", current_templates["fedora"]]
            )
        except subprocess.CalledProcessError as e:
            sdlog.error(
                "Failed to shut down {}".format(current_templates["fedora"])
            )
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
        sdlog.info(
            "Checking for updates {}:{}".format(vm, current_templates[vm])
        )
        subprocess.check_call(
            ["qvm-run", current_templates[vm], "sudo apt update"]
        )
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
            sdlog.error(
                "Failed to shut down {}".format(current_templates[vm])
            )
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
    return UpdateStatus.UPDATES_OK


class UpdateStatus(Enum):
    """
    Standardizes return codes for update/upgrade methods
    """
    UPDATES_OK = "UPDATES_OK"
    UPDATES_REQUIRED = "UPDATES_REQUIRED"
    UPDATES_FAILED = "UPDATES_FAILED"
    REBOOT_REQUIRED = "REBOOT_REQUIRED"
