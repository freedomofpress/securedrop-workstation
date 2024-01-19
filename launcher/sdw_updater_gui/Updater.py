#!/usr/bin/env python3
"""
Utility library for checking and applying SecureDrop Workstation VM updates.

This library is meant to be called by the SecureDrop launcher, which
is opened by the user when clicking on the desktop, opening sdw-laucher.py
from the parent directory.
"""

import json
import os
import subprocess
from datetime import datetime, timedelta
from enum import Enum
from sdw_util import Util

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_HOME = ".securedrop_launcher"
FLAG_FILE_STATUS_SD_APP = "/home/user/.securedrop_client/sdw-update-status"
FLAG_FILE_LAST_UPDATED_SD_APP = "/home/user/.securedrop_client/sdw-last-updated"
FLAG_FILE_STATUS_DOM0 = os.path.join(DEFAULT_HOME, "sdw-update-status")
FLAG_FILE_LAST_UPDATED_DOM0 = os.path.join(DEFAULT_HOME, "sdw-last-updated")
LOCK_FILE = "sdw-launcher.lock"
LOG_FILE = "launcher.log"
DETAIL_LOG_FILE = "launcher-detail.log"
DETAIL_LOGGER_PREFIX = "detail"  # For detailed logs such as Salt states

# We use a hardcoded temporary directory path in dom0. As dom0 is not
# a multi-user environment, we can safely assume that only the Updater is
# managing that filepath. Later on, we should consider porting the check-migration
# logic to leverage the Qubes Python API.
MIGRATION_DIR = "/tmp/sdw-migrations"  # nosec

DEBIAN_VERSION = "bullseye"

sdlog = Util.get_logger(module=__name__)
detail_log = Util.get_logger(prefix=DETAIL_LOGGER_PREFIX, module=__name__)

# The are the TemplateVMs that require full patch level at boot in order to start the client,
# as well as their associated TemplateVMs.
# In the future, we could use qvm-prefs to extract this information.
current_vms = {
    "fedora": "fedora-38",
    "sd-viewer": "sd-large-{}-template".format(DEBIAN_VERSION),
    "sd-app": "sd-small-{}-template".format(DEBIAN_VERSION),
    "sd-log": "sd-small-{}-template".format(DEBIAN_VERSION),
    "sd-devices": "sd-large-{}-template".format(DEBIAN_VERSION),
    "sd-proxy": "sd-small-{}-template".format(DEBIAN_VERSION),
    "sd-whonix": "whonix-gateway-17",
    "sd-gpg": "sd-small-{}-template".format(DEBIAN_VERSION),
}

current_templates = set([val for key, val in current_vms.items() if key != "dom0"])


def get_dom0_path(folder):
    return os.path.join(os.path.expanduser("~"), folder)


def run_full_install():
    """
    Re-apply the entire Salt config via sdw-admin. Required to enforce
    VM state during major migrations, such as template consolidation.
    """
    sdlog.info("Running 'sdw-admin --apply' to apply full system state")
    apply_cmd = ["sdw-admin", "--apply"]
    apply_cmd_for_log = (" ").join(apply_cmd)
    try:
        output = subprocess.check_output(apply_cmd)
    except subprocess.CalledProcessError as e:
        sdlog.error("Failed to apply full system state. Please review {}.".format(DETAIL_LOG_FILE))
        sdlog.error(str(e))
        clean_output = Util.strip_ansi_colors(e.output.decode("utf-8").strip())
        detail_log.error(
            "Output from failed command: {}\n{}".format(apply_cmd_for_log, clean_output)
        )
        return UpdateStatus.UPDATES_FAILED

    clean_output = Util.strip_ansi_colors(output.decode("utf-8").strip())
    detail_log.info("Output from command: {}\n{}".format(apply_cmd_for_log, clean_output))

    # Clean up flag requesting migration. Shell out since root created it.
    rm_flag_cmd = ["sudo", "rm", "-rf", MIGRATION_DIR]
    try:
        subprocess.check_call(rm_flag_cmd)
    except subprocess.CalledProcessError as e:
        sdlog.error("Failed to remove migration flag.")
        sdlog.error(str(e))
        return UpdateStatus.UPDATES_FAILED

    sdlog.info("Full system state successfully applied and migration flag cleared.")
    return UpdateStatus.UPDATES_OK


def migration_is_required():
    """
    Check whether a full run of the Salt config via sdw-admin is required.
    """
    result = False
    if os.path.exists(MIGRATION_DIR):
        if len(os.listdir(MIGRATION_DIR)) > 0:
            sdlog.info("Migration is required, will enforce full config during update")
            result = True
    return result


def apply_updates(vms=current_templates, progress_start=15, progress_end=75):
    """
    Apply updates to all TemplateVMs.

    Returns a tuple of (vm_name, percentage_progress, upgrade_results),
    for use in updating the GUI progress bar.
    """
    sdlog.info("Applying all updates to VMs: {}".format(vms))
    # Figure out how much each completed VM should bump the progress bar.
    assert progress_end > progress_start
    progress_step = (progress_end - progress_start) // len(vms)

    progress_current = progress_start

    for vm in vms:
        upgrade_results = UpdateStatus.UPDATES_FAILED
        if vm == "dom0":
            dom0_status = _check_updates_dom0()
            if dom0_status == UpdateStatus.UPDATES_REQUIRED:
                upgrade_results = _apply_updates_dom0()
            else:
                upgrade_results = UpdateStatus.UPDATES_OK
        else:
            upgrade_results = _apply_updates_vm(vm)

        progress_current += progress_step

        # constrain progress_current to given progress range
        def clamp(val, min_val, max_val):
            return max(min(max_val, val), min_val)

        progress_current = clamp(progress_current, progress_start, progress_end)

        yield vm, progress_current, upgrade_results


def _check_updates_dom0():
    """
    We need to reboot the system after every dom0 update. The update
    script does not tell us through its exit code whether updates were applied,
    and parsing command output can be brittle.

    For this reason, we check for available updates first. The result of this
    check is cached, so it does not incur a significant performance penalty.
    """
    try:
        subprocess.check_call(["sudo", "qubes-dom0-update", "--check-only"])
    except subprocess.CalledProcessError as e:
        sdlog.error("dom0 updates required, or cannot check for updates")
        sdlog.error(str(e))
        return UpdateStatus.UPDATES_REQUIRED

    sdlog.info("No updates available for dom0")
    return UpdateStatus.UPDATES_OK


def _apply_updates_dom0():
    """
    Apply updates to dom0. Any update to dom0 will require a reboot after
    the upgrade.
    """
    sdlog.info("Updating dom0")
    try:
        subprocess.check_call(["sudo", "qubes-dom0-update", "-y"])
    except subprocess.CalledProcessError as e:
        sdlog.error("An error has occurred updating dom0. Please contact your administrator.")
        sdlog.error(str(e))
        return UpdateStatus.UPDATES_FAILED

    sdlog.info("dom0 updates have been applied and a reboot is required.")
    return UpdateStatus.REBOOT_REQUIRED


def _apply_updates_vm(vm):
    """
    Apply updates to a given TemplateVM. Any update to the base fedora template
    will require a reboot after the upgrade.
    """
    sdlog.info("Updating {}".format(vm))

    # We run custom Salt logic for our own Debian-based TemplateVMs
    if vm.startswith("fedora") or vm.startswith("whonix"):
        salt_state = "update.qubes-vm"
    else:
        salt_state = "fpf-apt-repo"

    try:
        subprocess.check_call(
            ["sudo", "qubesctl", "--skip-dom0", "--targets", vm, "state.sls", salt_state]
        )
    except subprocess.CalledProcessError as e:
        sdlog.error(
            "An error has occurred updating {}. Please contact your administrator.".format(vm)
        )
        sdlog.error(str(e))
        return UpdateStatus.UPDATES_FAILED
    sdlog.info("{} update successful".format(vm))
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
            ["qvm-run", "sd-app", "echo '{}' > {}".format(status.value, flag_file_path_sd_app)]
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
        reboot_time = datetime.strptime(flag_contents["last_status_update"], DATE_FORMAT)
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

    delta = timedelta(hours=uptime_hours, minutes=uptime_minutes, seconds=uptime_seconds)

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


def apply_dom0_state():
    """
    Applies the dom0 state to ensure dom0 and AppVMs are properly
    Configured. This will *not* enforce configuration inside the AppVMs.
    Here, we call qubectl directly (instead of through sdw-admin) to
    ensure it is environment-specific.
    """
    sdlog.info("Applying dom0 state")
    cmd = ["sudo", "qubesctl", "--show-output", "state.highstate"]
    cmd_for_log = " ".join(cmd)
    try:
        output = subprocess.check_output(cmd)
        sdlog.info("Dom0 state applied")
        clean_output = Util.strip_ansi_colors(output.decode("utf-8").strip())
        detail_log.info("Output from command: {}\n{}".format(cmd_for_log, clean_output))
        return UpdateStatus.UPDATES_OK
    except subprocess.CalledProcessError as e:
        sdlog.error("Failed to apply dom0 state. See {} for details.".format(DETAIL_LOG_FILE))
        sdlog.error(str(e))
        clean_output = Util.strip_ansi_colors(e.output.decode("utf-8").strip())
        detail_log.error("Output from failed command: {}\n{}".format(cmd_for_log, clean_output))
        return UpdateStatus.UPDATES_FAILED


def shutdown_and_start_vms():
    """
    Power cycles the vms to ensure. we should do them all in one shot to reduce complexity
    and likelihood of failure. Rebooting the VMs will ensure the TemplateVM
    updates are picked up by the AppVM. We must first shut all VMs down to ensure
    correct order of operations, as sd-whonix cannot shutdown if sd-proxy is powered
    on, for example.

    All system AppVMs (sys-net, sys-firewall and sys-usb) need to be restarted.
    We use qvm-kill for sys-firewall and sys-net, because a shutdown may fail
    if they are currently in use as NetVMs by any of the user's other VMs.
    """

    sdw_vms_in_order = ["sd-app", "sd-proxy", "sd-whonix", "sd-gpg", "sd-log"]

    sdlog.info("Shutting down SDW TemplateVMs for updates")
    for vm in sorted(current_templates):
        _safely_shutdown_vm(vm)

    sdlog.info("Shutting down SDW AppVMs for updates")
    for vm in sdw_vms_in_order:
        _safely_shutdown_vm(vm)

    # System VMs that can be safely shut down (order should not matter, but will
    # be respected).
    safe_sys_vms_in_order = ["sys-usb", "sys-whonix"]
    for vm in safe_sys_vms_in_order:
        sdlog.info("Safely shutting down system VM: {}".format(vm))
        _safely_shutdown_vm(vm)

    # TODO: Use of qvm-kill should be considered unsafe and may have unexpected
    # side effects. We should aim for a more graceful shutdown strategy.
    unsafe_sys_vms_in_order = ["sys-firewall", "sys-net"]
    for vm in unsafe_sys_vms_in_order:
        sdlog.info("Killing system VM: {}".format(vm))
        try:
            subprocess.check_output(["qvm-kill", vm], stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            sdlog.error("Error while killing system VM: {}".format(vm))
            sdlog.error(str(e))
            sdlog.error(str(e.stderr))

    all_sys_vms_in_order = safe_sys_vms_in_order + unsafe_sys_vms_in_order
    sdlog.info("Starting fedora-based system VMs after updates")
    for vm in reversed(all_sys_vms_in_order):
        _safely_start_vm(vm)

    sdlog.info("Starting SDW VMs after updates")
    for vm in reversed(sdw_vms_in_order):
        _safely_start_vm(vm)


def _safely_shutdown_vm(vm):
    try:
        subprocess.check_output(["qvm-shutdown", "--wait", vm], stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        sdlog.error("Failed to shut down {}".format(vm))
        sdlog.error(str(e))
        sdlog.error(str(e.stderr))
        return UpdateStatus.UPDATES_FAILED


def _safely_start_vm(vm):
    try:
        running_vms = subprocess.check_output(
            ["qvm-ls", "--running", "--raw-list"], stderr=subprocess.PIPE
        )
        sdlog.info("VMs running before start of {}: {}".format(vm, running_vms))
        subprocess.check_output(["qvm-start", "--skip-if-running", vm], stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        sdlog.error("Error while starting {}".format(vm))
        sdlog.error(str(e))
        sdlog.error(str(e.stderr))


def should_launch_updater(interval):
    status = read_dom0_update_flag_from_disk(with_timestamp=True)

    if _valid_status(status):
        if _interval_expired(interval, status):
            sdlog.info("Update interval expired: launching updater.")
            return True
        else:
            if status["status"] == UpdateStatus.UPDATES_OK.value:
                sdlog.info("Updates OK and interval not expired, launching client.")
                return False
            elif status["status"] == UpdateStatus.REBOOT_REQUIRED.value:
                if last_required_reboot_performed():
                    sdlog.info("Required reboot performed, updating status and launching client.")
                    _write_updates_status_flag_to_disk(UpdateStatus.UPDATES_OK)
                    return False
                else:
                    sdlog.info("Required reboot pending, launching updater")
                    return True
            elif status["status"] == UpdateStatus.UPDATES_REQUIRED.value:
                sdlog.info("Updates are required, launching updater.")
                return True
            elif status["status"] == UpdateStatus.UPDATES_FAILED.value:
                sdlog.info("Preceding update failed, launching updater.")
                return True
            else:
                sdlog.info("Update status is unknown, launching updater.")
                return True
    else:
        sdlog.info("Update status not available, launching updater.")
        return True


def _valid_status(status):
    """
    status should contain 2 items, the update flag and a timestamp.
    """
    if isinstance(status, dict) and len(status) == 2:
        return True
    return False


def _interval_expired(interval, status):
    """
    Check if specified update interval has expired.
    """

    try:
        update_time = datetime.strptime(status["last_status_update"], DATE_FORMAT)
    except ValueError:
        # Broken timestamp? run the updater.
        return True
    if (datetime.now() - update_time) < timedelta(seconds=interval):
        return False
    return True


class UpdateStatus(Enum):
    """
    Standardizes return codes for update/upgrade methods
    """

    UPDATES_OK = "0"
    UPDATES_REQUIRED = "1"
    REBOOT_REQUIRED = "2"
    UPDATES_FAILED = "3"
