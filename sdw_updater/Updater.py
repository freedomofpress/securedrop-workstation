"""
Utility library for checking and applying SecureDrop Workstation VM updates.

This library is meant to be called by the SecureDrop launcher, which
is opened by the user when clicking on the desktop, opening
/usr/bin/sdw-updater.
"""

import json
import os
import subprocess
import threading
import time
from datetime import datetime, timedelta
from enum import Enum

from sdw_util import Util

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_HOME = ".securedrop_updater"
FLAG_FILE_STATUS_SD_APP = "/home/user/.securedrop_client/sdw-update-status"
FLAG_FILE_LAST_UPDATED_SD_APP = "/home/user/.securedrop_client/sdw-last-updated"
FLAG_FILE_STATUS_DOM0 = os.path.join(DEFAULT_HOME, "sdw-update-status")
FLAG_FILE_LAST_UPDATED_DOM0 = os.path.join(DEFAULT_HOME, "sdw-last-updated")
LOCK_FILE = "sdw-updater.lock"
LOG_FILE = "updater.log"
DETAIL_LOG_FILE = "updater-detail.log"
DETAIL_LOGGER_PREFIX = "detail"  # For detailed logs such as Salt states

# We use a hardcoded temporary directory path in dom0. As dom0 is not
# a multi-user environment, we can safely assume that only the Updater is
# managing that filepath. Later on, we should consider porting the check-migration
# logic to leverage the Qubes Python API.
MIGRATION_DIR = "/tmp/sdw-migrations"

DEBIAN_VERSION = "bookworm"

sdlog = Util.get_logger(module=__name__)
detail_log = Util.get_logger(prefix=DETAIL_LOGGER_PREFIX, module=__name__)

# The are the TemplateVMs that require full patch level at boot in order to start the client,
# as well as their associated TemplateVMs.
# In the future, we could use qvm-prefs to extract this information.
current_vms = {
    "fedora": "fedora-40-xfce",
    "sd-viewer": f"sd-large-{DEBIAN_VERSION}-template",
    "sd-app": f"sd-small-{DEBIAN_VERSION}-template",
    "sd-log": f"sd-small-{DEBIAN_VERSION}-template",
    "sd-devices": f"sd-large-{DEBIAN_VERSION}-template",
    "sd-proxy": f"sd-small-{DEBIAN_VERSION}-template",
    "sd-whonix": "whonix-gateway-17",
    "sd-gpg": f"sd-small-{DEBIAN_VERSION}-template",
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
        sdlog.error(f"Failed to apply full system state. Please review {DETAIL_LOG_FILE}.")
        sdlog.error(str(e))
        clean_output = Util.strip_ansi_colors(e.output.decode("utf-8").strip())
        detail_log.error(f"Output from failed command: {apply_cmd_for_log}\n{clean_output}")
        return UpdateStatus.UPDATES_FAILED

    clean_output = Util.strip_ansi_colors(output.decode("utf-8").strip())
    detail_log.info(f"Output from command: {apply_cmd_for_log}\n{clean_output}")

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
    if os.path.exists(MIGRATION_DIR) and len(os.listdir(MIGRATION_DIR)) > 0:
        sdlog.info("Migration is required, will enforce full config during update")
        result = True
    return result


def apply_updates_dom0():
    """
    Apply updates to dom0
    """
    sdlog.info("Applying all updates to dom0")

    dom0_status = _check_updates_dom0()
    if dom0_status == UpdateStatus.UPDATES_REQUIRED:
        upgrade_results = _apply_updates_dom0()
    else:
        upgrade_results = UpdateStatus.UPDATES_OK
    return upgrade_results


def apply_updates_templates(templates=current_templates, progress_callback=None):
    """
    Apply updates to all TemplateVMs.
    """
    sdlog.info(f"Applying all updates to VMs: {', '.join(templates)}")
    try:
        proc = _start_qubes_updater_proc(templates)
        result_update_status = {}
        stderr_thread = threading.Thread(
            target=_qubes_updater_parse_progress,
            args=(proc.stderr, result_update_status, templates, progress_callback),
        )
        stdout_thread = threading.Thread(target=_qubes_updater_parse_stdout, args=(proc.stdout,))
        stderr_thread.start()
        stdout_thread.start()

        while proc.poll() is None or stderr_thread.is_alive() or stdout_thread.is_alive():
            time.sleep(1)

        stderr_thread.join()
        stdout_thread.join()
        proc.stderr.close()
        proc.stdout.close()
        update_status = overall_update_status(result_update_status)
        if update_status == UpdateStatus.UPDATES_OK:
            sdlog.info("Template updates successful")
        else:
            sdlog.info("Template updates failed")
        return update_status

    except subprocess.CalledProcessError as e:
        sdlog.error(
            "An error has occurred updating templates. Please contact your administrator."
            f" See {DETAIL_LOG_FILE} for details."
        )
        sdlog.error(str(e))
        return UpdateStatus.UPDATES_FAILED


def _start_qubes_updater_proc(templates):
    update_cmd = [
        "qubes-vm-update",
        "--apply-to-all",  # Enforce app qube restarts
        "--force-update",  # Bypass Qubes' staleness-dection and update all
        "--show-output",  # Update transaction details (goes to stdout)
        "--just-print-progress",  # Progress reporting (goes to stderr)
        "--targets",
        ",".join(templates),
    ]
    detail_log.info("Starting Qubes Updater with command: {}".format(" ".join(update_cmd)))
    return subprocess.Popen(
        update_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _qubes_updater_parse_stdout(stream):
    while True:
        untrusted_line = stream.readline()
        if len(untrusted_line) == 0:
            break

        line = Util.strip_ansi_colors(untrusted_line.decode("utf-8"))
        line = line.rstrip()
        detail_log.info(f"[Qubes updater] {line}")


def _qubes_updater_parse_progress(stream, result, templates, progress_callback=None):
    update_progress = {}

    for template in templates:
        result[template] = UpdateStatus.UPDATES_IN_PROGRESS

    while True:
        untrusted_line = stream.readline()
        if len(untrusted_line) == 0:
            break

        line = Util.strip_ansi_colors(untrusted_line.decode("utf-8").rstrip())
        try:
            vm, status, info = line.split()
        except ValueError:
            sdlog.warn("Line in Qubes updater's output could not be parsed")
            continue

        if status == "updating":
            if update_progress.get(vm) is None:
                sdlog.info(f"Starting update on template: '{vm}'")
                update_progress[vm] = 0
            else:
                vm_progress = int(float(info))
                update_progress[vm] = vm_progress
                if progress_callback:
                    progress_callback(sum(update_progress.values()) // len(templates))

        # First time complete (status "done") may be repeated various times
        if status == "done" and result[vm] == UpdateStatus.UPDATES_IN_PROGRESS:
            result[vm] = UpdateStatus.from_qubes_updater_name(info)
            if result[vm] == UpdateStatus.UPDATES_OK:
                sdlog.info(f"Update successful for template: '{vm}'")
                update_progress[vm] = 100
            else:
                sdlog.error(f"Update failed for template: '{vm}'")


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


def _write_last_updated_flags_to_disk():
    """
    Writes the time of last successful upgrade to dom0 and sd-app
    """
    current_date = str(datetime.now().strftime(DATE_FORMAT))

    flag_file_sd_app_last_updated = FLAG_FILE_LAST_UPDATED_SD_APP
    flag_file_dom0_last_updated = get_dom0_path(FLAG_FILE_LAST_UPDATED_DOM0)

    try:
        sdlog.info(f"Setting last updated to {current_date} in sd-app")
        subprocess.check_call(
            [
                "qvm-run",
                "sd-app",
                f"echo '{current_date}' > {flag_file_sd_app_last_updated}",
            ]
        )
    except subprocess.CalledProcessError as e:
        sdlog.error("Error writing last updated flag to sd-app")
        sdlog.error(str(e))

    try:
        sdlog.info(f"Setting last updated to {current_date} in dom0")
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
        sdlog.info(f"Setting update flag to {status.value} in sd-app")
        subprocess.check_call(
            ["qvm-run", "sd-app", f"echo '{status.value}' > {flag_file_path_sd_app}"]
        )
    except subprocess.CalledProcessError as e:
        sdlog.error("Error writing update status flag to sd-app")
        sdlog.error(str(e))

    try:
        sdlog.info(f"Setting update flag to {status.value} in dom0")
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

        # If we booted after the reboot time, the restart happened
        return boot_time >= reboot_time

    # previous run did not require reboot
    return True


def _get_uptime():
    """
    Returns timedelta containing system (dom0) uptime.
    """
    uptime = None
    with open("/proc/uptime") as f:
        uptime = f.read().split(" ")[0].strip()
    uptime = int(float(uptime))
    uptime_hours = uptime // 3600
    uptime_minutes = (uptime % 3600) // 60
    uptime_seconds = uptime % 60

    return timedelta(hours=uptime_hours, minutes=uptime_minutes, seconds=uptime_seconds)


def read_dom0_update_flag_from_disk(with_timestamp=False):
    """
    Read the last updated SecureDrop Workstation update status from disk
    in dom0, and returns the corresponding UpdateStatus. If ivoked the
    parameter `with_timestamp=True`, this function will return the full json.
    """
    flag_file_path_dom0 = get_dom0_path(FLAG_FILE_STATUS_DOM0)

    try:
        with open(flag_file_path_dom0) as f:
            contents = json.load(f)
            for status in UpdateStatus:
                if int(contents["status"]) == int(status.value):
                    if with_timestamp:
                        return contents

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
        if result == UpdateStatus.UPDATES_IN_PROGRESS:
            updates_failed = True
        elif result == UpdateStatus.REBOOT_REQUIRED:
            reboot_required = True
        elif result == UpdateStatus.UPDATES_REQUIRED:
            updates_required = True

    if updates_failed:
        return UpdateStatus.UPDATES_FAILED
    if reboot_required:
        return UpdateStatus.REBOOT_REQUIRED
    if updates_required:
        return UpdateStatus.UPDATES_REQUIRED

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
        detail_log.info(f"Output from command: {cmd_for_log}\n{clean_output}")
        return UpdateStatus.UPDATES_OK
    except subprocess.CalledProcessError as e:
        sdlog.error(f"Failed to apply dom0 state. See {DETAIL_LOG_FILE} for details.")
        sdlog.error(str(e))
        clean_output = Util.strip_ansi_colors(e.output.decode("utf-8").strip())
        detail_log.error(f"Output from failed command: {cmd_for_log}\n{clean_output}")
        return UpdateStatus.UPDATES_FAILED


def should_launch_updater(interval):
    status = read_dom0_update_flag_from_disk(with_timestamp=True)

    if _valid_status(status):
        if _interval_expired(interval, status):
            sdlog.info("Update interval expired: launching updater.")
            return True
        if status["status"] == UpdateStatus.UPDATES_OK.value:
            sdlog.info("Updates OK and interval not expired, launching client.")
            return False
        if status["status"] == UpdateStatus.REBOOT_REQUIRED.value:
            if last_required_reboot_performed():
                sdlog.info("Required reboot performed, updating status and launching client.")
                _write_updates_status_flag_to_disk(UpdateStatus.UPDATES_OK)
                return False

            sdlog.info("Required reboot pending, launching updater")
            return True
        if status["status"] == UpdateStatus.UPDATES_REQUIRED.value:
            sdlog.info("Updates are required, launching updater.")
            return True
        if status["status"] == UpdateStatus.UPDATES_FAILED.value:
            sdlog.info("Preceding update failed, launching updater.")
            return True

        sdlog.info("Update status is unknown, launching updater.")
        return True

    sdlog.info("Update status not available, launching updater.")
    return True


def _valid_status(status):
    """
    status should contain 2 items, the update flag and a timestamp.
    """
    return isinstance(status, dict) and len(status) == 2


def _interval_expired(interval, status):
    """
    Check if specified update interval has expired.
    """

    try:
        update_time = datetime.strptime(status["last_status_update"], DATE_FORMAT)
    except ValueError:
        # Broken timestamp? run the updater.
        return True
    return (datetime.now() - update_time) >= timedelta(seconds=interval)


class UpdateStatus(Enum):
    """
    Standardizes return codes for update/upgrade methods
    """

    UPDATES_OK = "0"
    UPDATES_REQUIRED = "1"
    REBOOT_REQUIRED = "2"
    UPDATES_FAILED = "3"
    UPDATES_IN_PROGRESS = "4"

    @classmethod
    def from_qubes_updater_name(cls, name):
        """
        Maps qubes updater's terminology to SDW Updater one. Upstream code found in:
        https://github.com/QubesOS/qubes-desktop-linux-manager/blob/4afc35/qui/updater/utils.py#L199C25-L204C27
        """
        names = {
            "success": cls.UPDATES_OK,
            "error": cls.UPDATES_FAILED,
            "no_updates": cls.UPDATES_OK,
            "cancelled": cls.UPDATES_FAILED,
        }
        try:
            return names[name]
        except KeyError:
            sdlog.error("Qubes updater provided an invalid update status.")
            return cls.UPDATES_FAILED
