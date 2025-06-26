#!/usr/bin/python3
"""
Admin wrapper script for applying salt states for staging and prod scenarios. The rpm
packages only puts the files in place `/srv/salt` but does not apply the state, nor
does it handle the config.
"""

import argparse
import json
import os
import subprocess
import sys

from qubesadmin import Qubes

from sdw_util import Util

# The max concurrency reduction (4->2) was required to avoid "did not return clean data"
# errors from qubesctl. It may be possible to raise this again.
MAX_CONCURRENCY = 2

DEFAULT_SD_APP_GB = 10
DEFAULT_SD_LOG_GB = 5

SCRIPTS_PATH = "/usr/share/securedrop-workstation-dom0-config/"
SALT_PATH = "/srv/salt/securedrop_salt/"
BASE_TEMPLATE = "debian-12-minimal"

SUBMISSION_KEY = "sd-journalist.sec"
TAILS_PATH = "/run/media/user/TailsData/"
TAILS_GNUPG_PATH = TAILS_PATH + "gnupg/"
TAILS_JOURNALIST_INTERFACE_CONFIG = (
    TAILS_PATH + "Persistent/securedrop/install_files/ansible-base/app-journalist.auth_private"
)

sys.path.insert(1, os.path.join(SCRIPTS_PATH, "scripts/"))
from validate_config import SDWConfigValidator, ValidationError  # noqa: E402

DEBIAN_VERSION = "bookworm"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        default=False,
        required=False,
        action="store_true",
        help="Apply workstation configuration with Salt",
    )
    parser.add_argument(
        "--validate",
        default=False,
        required=False,
        action="store_true",
        help="Validate the configuration",
    )
    parser.add_argument(
        "--uninstall",
        default=False,
        required=False,
        action="store_true",
        help="Completely Uninstalls the SecureDrop Workstation",
    )
    parser.add_argument(
        "--force",
        default=False,
        required=False,
        action="store_true",
        help="During uninstall action, don't prompt for confirmation, proceed immediately",
    )
    parser.add_argument(
        "--configure",
        default=False,
        required=False,
        action="store_true",
        help="Configure SecureDrop Workstation",
    )
    return parser.parse_args()


def install_pvh_support():
    """
    Installs grub2-xen-pvh in dom0 - required for PVH with AppVM local kernels
    TODO: install this via package requirements instead if possible
    """
    try:
        subprocess.check_call(["sudo", "qubes-dom0-update", "-y", "-q", "grub2-xen-pvh"])
    except subprocess.CalledProcessError:
        raise SDWAdminException("Error installing grub2-xen-pvh: local PVH not available.")


def copy_config():
    """
    Copies config.json and sd-journalist.sec to /srv/salt/securedrop_salt
    """
    try:
        subprocess.check_call(["sudo", "cp", os.path.join(SCRIPTS_PATH, "config.json"), SALT_PATH])
        subprocess.check_call(
            ["sudo", "cp", os.path.join(SCRIPTS_PATH, "sd-journalist.sec"), SALT_PATH]
        )
    except subprocess.CalledProcessError:
        raise SDWAdminException("Error copying configuration")


def provision_and_configure():
    """
    Applies the salt state.highstate on dom0 and all VMs
    """
    provision("Provisioning Fedora-based system VMs", "securedrop_salt.sd-sys-vms")
    provision("Provisioning base template", "securedrop_salt.sd-base-template")
    configure("Configuring base template", ["sd-base-bookworm-template"])
    provision_all()
    configure("Enabling Whonix customizations", [f"whonix-gateway-{Util.get_whonix_version()}"])
    configure(
        "Configure all SecureDrop Workstation VMs with service-specific configs",
        [q.name for q in Qubes().domains if "sd-workstation" in q.tags],
    )

    sync_appmenus()

    if "sd-fedora-41-dvm" in Qubes().domains:
        # If sd-fedora-41-dvm exists it's because salt determined that sys-usb was disposable
        configure(
            "Add SecureDrop export device handling to sys-usb (disposable)",
            ["sd-fedora-41-dvm"],
            restart=["sys-usb"],
        )
    else:
        configure(
            "Add SecureDrop export device handling to sys-usb (non-disposable)",
            ["sys-usb"],
        )

    print("Provisioning complete. Please reboot to complete the installation.")


def run_cmd(args):
    print(f"Running \"{' '.join(args)}\"")
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError:
        raise SDWAdminException(f"Error while running {' '.join(args)}")


def provision(step_description: str, salt_state: str):
    """
    Create, change or delete qubes
    """

    qubesctl_call(step_description, ["--", "state.sls", salt_state])


def provision_all():
    """
    Provision all enabled salt states
    """
    qubesctl_call(
        "Set up dom0 config files, including RPC policies, and create VMs", ["state.highstate"]
    )


def configure(step_description: str, targets: list[str], restart: list[str] | None = None):
    """
    Apply configuration to a list of qubes
    """

    qubesctl_call(
        step_description,
        [
            "--skip-dom0",
            "--max-concurrency",
            str(MAX_CONCURRENCY),
            "--targets",
            ",".join(targets),
            "state.highstate",
        ],
    )

    # Save new configuration to disk by shutting down
    run_cmd(["qvm-shutdown", "--wait", "--"] + targets)

    if restart:
        run_cmd(["qvm-shutdown", "--wait", "--"] + restart)
        run_cmd(["qvm-start", "--"] + restart)


def qubesctl_call(step_description: str, args: list[str]):
    qubesctl_cmd = ["sudo", "qubesctl", "--show-output"] + args
    print("\n..........................................................................")
    print(step_description)
    print(f"Running \"{' '.join(qubesctl_cmd)}\"")

    try:
        subprocess.check_call(qubesctl_cmd)
    except subprocess.CalledProcessError:
        raise SDWAdminException(f"Error in step {step_description}")


def sync_appmenus():
    """
    Sync appmenus now that all packages are installed
    TODO: this should be done by salt or debs, but we do it manually here because it's
    not straightforward to run a dom0 salt state after VMs run.
    n.b. none of the small VMs are shown in the menu on prod, but nice to have it synced
    """

    run_cmd(["qvm-start", "--skip-if-running", "sd-small-bookworm-template"])
    run_cmd(["qvm-sync-appmenus", "sd-small-bookworm-template"])
    run_cmd(["qvm-shutdown", "sd-small-bookworm-template"])

    run_cmd(["qvm-start", "--skip-if-running", "sd-large-bookworm-template"])
    run_cmd(["qvm-sync-appmenus", "sd-large-bookworm-template"])
    run_cmd(["qvm-shutdown", "sd-large-bookworm-template"])

    whonix_gateway = f"whonix-gateway-{Util.get_whonix_version()}"
    run_cmd(["qvm-start", "--skip-if-running", whonix_gateway])
    run_cmd(["qvm-sync-appmenus", whonix_gateway])
    run_cmd(["qvm-shutdown", whonix_gateway])

    # These are the ones we show in prod VMs, so sync explicitly
    run_cmd(["qvm-sync-appmenus", "--regenerate-only", "sd-devices"])
    run_cmd(["qvm-sync-appmenus", "--regenerate-only", "sd-whonix"])
    run_cmd(["qvm-sync-appmenus", "--regenerate-only", "sd-log"])


def validate_config(path):
    """
    Calls the validate_config script to validate the config present in the staging/prod directory
    """
    try:
        validator = SDWConfigValidator(path)  # noqa: F841
    except ValidationError:
        raise SDWAdminException("Error while validating configuration")


def get_appvms_for_template(vm_name: str) -> list[str]:
    """
    Return a list of AppVMs that use the specified VM as a template
    """
    app = Qubes()
    try:
        template_vm = app.domains[vm_name]
    except KeyError:
        # No VM implies no appvms, return an empty list
        # (The template may just not be installed yet)
        return []
    return [x.name for x in list(template_vm.appvms)]


def refresh_salt():
    """
    Cleans the Salt cache and synchronizes Salt to ensure we are applying states
    from the currently installed version
    """
    try:
        subprocess.check_call(["sudo", "rm", "-rf", "/var/cache/salt"])
    except subprocess.CalledProcessError:
        raise SDWAdminException("Error while clearing Salt cache")

    try:
        subprocess.check_call(["sudo", "qubesctl", "saltutil.sync_all", "refresh=true"])
    except subprocess.CalledProcessError:
        raise SDWAdminException("Error while synchronizing Salt")


def perform_uninstall():
    try:
        subprocess.check_call(
            ["sudo", "qubesctl", "state.sls", "securedrop_salt.sd-clean-default-dispvm"]
        )
        print("Destroying all VMs")
        provision("Removing unused SDW qubes", "securedrop_salt.sd-remove-deprecated-qubes")
        subprocess.check_call([os.path.join(SCRIPTS_PATH, "scripts/destroy-vm"), "--all-tagged"])
        print("Reverting dom0 configuration")
        subprocess.check_call(["sudo", "qubesctl", "state.sls", "securedrop_salt.sd-clean-all"])
        subprocess.check_call([os.path.join(SCRIPTS_PATH, "scripts/clean-salt")])
        print("Uninstalling dom0 config package")
        subprocess.check_call(
            ["sudo", "dnf", "-y", "-q", "remove", "securedrop-workstation-dom0-config"]
        )
    except subprocess.CalledProcessError:
        raise SDWAdminException("Error during uninstall")

    print(
        "Instance secrets (Journalist Interface token and Submission private key) are still "
        "present on disk. You can delete them in /usr/share/securedrop-workstation-dom0-config"
    )


def extract_secret_key_fingerprints(gpg_output):
    """
    Parses gpg output to return fingerprints for all secret keys in the keyring.
    """
    lines = gpg_output.strip().split("\n")
    fingerprints = []

    primary_key = True
    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        if idx >= len(lines) - 1:
            continue
        
        fields = line.split(":")
        record_type = fields[0]

        # Secret key
        if record_type == "sec":
            # Following line should be the secret key fingerprint
            fpr_fields = lines[idx+1].split(":")
            if fpr_fields[0] == "fpr" and len(fpr_fields) > 9 and fpr_fields[9]:
                fingerprints.append(fpr_fields[9])

    return fingerprints


def _try_read_submission_key():
    """
    Checks if SecureDrop submission key is written to dom0. If so, returns
    submission key fingerprint
    """
    if not os.path.exists(SCRIPTS_PATH + SUBMISSION_KEY):
        return None
    gpg_output = subprocess.check_output(
        ["gpg", "--show-keys", "--with-fingerprint", "--with-colon", SCRIPTS_PATH + SUBMISSION_KEY],
        text=True,
    )
    return extract_fingerprint(gpg_output)


def _prompt_choose_submission_key(fingerprints):
    print(
        "Multiple eligible secret keys found in the keyring.\n"
        "Please select which secret key to use as the SecureDrop submission key.\n\n"
    )
    for i, fpr_option in enumerate(fingerprints, 1):
        print(f"{i}. {fpr_option}")
    try:
        choice = int(input(f"Submission key [1-{len(fingerprints)}]: "))
        if 1 <= choice <= len(options): 
            fingerprint = fingerprints[choice-1]
            print(f"Selected key {choice}: {fingerprint}")
            return fingerprint
        else:
            print("Invalid choice. Exiting.")
            return None
    except ValueError:
        print("Invalid input. Exiting.")
        return None

def import_submission_key():
    """
    Imports SecureDrop submission key from USB drive to dom0. Assumes that the USB drive
    is successfully attached to vault VM and decrypted.
    Returns the submission key fingerprint.
    """
    gpg_output = subprocess.check_output(
        [
            "qvm-run",
            "--pass-io",
            "vault",
            f"gpg --homedir {TAILS_GNUPG_PATH} -K --fingerprint --with-colon",
        ],
        text=True,
    )
    fingerprints = extract_secret_key_fingerprints(gpg_output)
    if len(fingerprints) == 0:
        raise SDWAdminException("Error reading submission key fingerprint: no private keys found")
    if len(fingerprints) > 1:
        fingerprint = _prompt_choose_submission_key(fingerprints)
        if not fingerprint:
            raise SDWAdminException("Error importing submission key: unable to select from multiple eligible keys")
    else:
        fingerprint = fingerprints[0]

    gpg_privkey = subprocess.check_output(
        [
            "qvm-run",
            "--pass-io",
            "vault",
            f"gpg --homedir {TAILS_GNUPG_PATH} --export-secret-keys --armor {fingerprint}",
        ],
        text=True,
    )

    temp_file = "/tmp/sd-journalist.sec"
    with open(temp_file, "w") as f:
        f.write(gpg_privkey)

    subprocess.check_call(["sudo", "cp", temp_file, SCRIPTS_PATH])

    return fingerprint


def import_journalist_interface_config():
    """
    Imports Journalist Interface address and authentication info from USB drive to dom0.
    Assumes that USB drive is attached to vault VM and decrypted.
    Returns (hostname, key) of the journalist interface hidserv
    """
    journalist_interface_config = subprocess.check_output(
        [
            "qvm-run",
            "--pass-io",
            "vault",
            f"cat {TAILS_JOURNALIST_INTERFACE_CONFIG}",
        ],
        text=True,
    )
    fields = journalist_interface_config.strip().split(":")
    addr = fields[0]
    auth_token = fields[3]
    return addr, auth_token


def import_config():
    submission_key_fingerprint = _try_read_submission_key()
    if not submission_key_fingerprint:
        subprocess.Popen(
            ["qvm-start", "vault"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print(
            "Importing SecureDrop submission key from USB...\n\n\n"
            "Ensure that USB containing submission key is connected.\n\n"
            "1. Attach the USB to the vault VM\n"
            "2. Open Thunar File Manager in the vault VM\n"
            "3. Select the USB drive in the left sidebar of the file manager.\n"
            "It should be listed under Devices as 'N GB Encrypted'.\n"
            "Enter the correct passphrase when prompted.\n\n"
        )
        response = input("Are you ready to proceed (y/N)?")
        if response.lower() != "y":
            print("Exiting.")
            return
        print("Importing submission key...")
        submission_key_fingerprint = import_submission_key()
        print(
            "Submission key import complete!\n"
            "Please detach and disconnect the USB containing the submission key\n\n"
        )
    else:
        print("Found submission key file, proceeding")

    try:
        validate_config(SCRIPTS_PATH)
        print("Valid configuration found, configuration complete")
    except SDWAdminException:
        subprocess.Popen(
            ["qvm-start", "vault"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print(
            "Importing Journalist Interface details...\n\n\n"
            "Ensure that Admin Workstation or Journalist Workstation USB is connected.\n\n"
            "1. Attach the USB to the vault VM\n"
            "2. Open Thunar File Manager in the vault VM\n"
            "3. Select the USB drive in the left sidebar of the file manager.\n"
            "It should be listed under Devices as 'N GB Encrypted'.\n"
            "Enter the correct passphrase when prompted.\n\n"
        )
        response = input("Are you ready to proceed (y/N)?")
        if response.lower() != "y":
            print("Exiting.")
            return
        ji_addr, ji_auth_token = import_journalist_interface_config()
        print(
            "Journalist Interface details imported.\n\n"
            f"Onion address: {ji_addr}.onion\n"
            f"Auth token: {ji_auth_token}\n"
        )
        resonse = input("Confirm that these values are correct to proceed (y/N)")
        if response.lower() != "y":
            print("Exiting.")
            return

        # Configure private volume sizes
        sd_app_gb = input(
            f"Enter desired size for sd-app private volume in GiB (default: {DEFAULT_SD_APP_GB}GiB)"
        )
        if not sd_app_gb:
            sd_app_gb = DEFAULT_SD_APP_GB
        sd_log_gb = input(
            f"Enter desired size for sd-log private volume in GiB (default: {DEFAULT_SD_LOG_GB}GiB)"
        )
        if not sd_log_gb:
            sd_log_gb = DEFAULT_SD_LOG_GB

        config = {
            "submission_key_fpr": submission_key_fingerprint,
            "hidserv": {
                "hostname": ji_addr + ".onion",
                "key": ji_auth_token,
            },
            "environment": "prod",
            "vmsizes": {"sd_app": sd_app_gb, "sd_log": sd_log_gb},
        }
        temp_file = "/tmp/config.json"
        with open(temp_file, "w") as f:
            json.dump(config, f, indent=2)
        subprocess.check_call(["sudo", "cp", temp_file, SCRIPTS_PATH])
        print(
            "Journalist Interface import complete!\n"
            "Please detach and disconnect the USB drive.\n\n"
        )
        print("Validating configuration...")
        validate_config(SCRIPTS_PATH)
        print("Validation successful!")
    return


def main():
    if os.geteuid() == 0:
        print("Please do not run this script as root.")
        sys.exit(0)
    args = parse_args()
    if args.validate:
        print("Validating...", end="")
        validate_config(SCRIPTS_PATH)
        print("OK")
    elif args.apply:
        print(
            "SecureDrop Workstation should be installed on a fresh Qubes OS install.\n"
            "The installation process will overwrite any user modifications to the\n"
            f"{BASE_TEMPLATE} TemplateVM, and will disable old-format qubes-rpc\n"
            "policy directives.\n"
        )
        affected_appvms = get_appvms_for_template(BASE_TEMPLATE)
        if len(affected_appvms) > 0:
            print(
                f"{BASE_TEMPLATE} is already in use by the following AppVMS:\n"
                f"{affected_appvms}\n"
                "Applications and configurations in use by these AppVMs will be\n"
                f"removed from {BASE_TEMPLATE}."
            )
            response = input("Are you sure you want to proceed (y/N)? ")
            if response.lower() != "y":
                print("Exiting.")
                sys.exit(0)
        print("Applying configuration...")
        validate_config(SCRIPTS_PATH)
        install_pvh_support()
        copy_config()
        refresh_salt()
        provision_and_configure()
    elif args.uninstall:
        print(
            "Uninstalling will remove all packages and destroy all VMs associated\n"
            "with SecureDrop Workstation. It will also remove all SecureDrop tags\n"
            "from other VMs on the system."
        )
        if not args.force:
            response = input("Are you sure you want to uninstall (y/N)? ")
            if response.lower() != "y":
                print("Exiting.")
                sys.exit(0)
        refresh_salt()
        perform_uninstall()
    elif args.configure:
        print(
            "Preparing to import SecureDrop Workstation configuration...\n\n"
            "Make sure you have the USB with the submission key and an\n"
            "Admin Workstation or Journalist Workstation USB drive accessible.\n\n\n"
        )
        import_config()
    else:
        sys.exit(0)


class SDWAdminException(Exception):
    pass


if __name__ == "__main__":
    main()
