#!/usr/bin/python3
"""
Admin wrapper script for applying salt states for staging and prod scenarios. The rpm
packages only puts the files in place `/srv/salt` but does not apply the state, nor
does it handle the config.
"""

import argparse
import os
import subprocess
import sys
from typing import List, Optional

from qubesadmin import Qubes

# The max concurrency reduction (4->2) was required to avoid "did not return clean data"
# errors from qubesctl. It may be possible to raise this again.
MAX_CONCURRENCY = 2

SCRIPTS_PATH = "/usr/share/securedrop-workstation-dom0-config/"
SALT_PATH = "/srv/salt/securedrop_salt/"
BASE_TEMPLATE = "debian-12-minimal"

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
    configure(
        "Configuring template for log sink before anything else",
        ["sd-small-bookworm-template"],
        restart=["sd-log"],
    )
    configure("Enabling Whonix customizations", ["whonix-gateway-17"])
    configure(
        "Configure all SecureDrop Workstation VMs with service-specific configs",
        [q.name for q in Qubes().domains if "sd-workstation" in q.tags],
    )

    sync_appmenus()

    if "sd-fedora-40-dvm" in Qubes().domains:
        # If sd-fedora-40-dvm exists it's because salt determined that sys-usb was disposable
        configure(
            "Add SecureDrop export device handling to sys-usb (disposable)",
            ["sd-fedora-40-dvm"],
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


def configure(step_description: str, targets: List[str], restart: Optional[List[str]] = None):
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


def qubesctl_call(step_description: str, args: List[str]):
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

    run_cmd(["qvm-start", "--skip-if-running", "whonix-gateway-17"])
    run_cmd(["qvm-sync-appmenus", "whonix-gateway-17"])
    run_cmd(["qvm-shutdown", "whonix-gateway-17"])

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


def get_appvms_for_template(vm_name: str) -> List[str]:
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
        subprocess.check_call([os.path.join(SCRIPTS_PATH, "scripts/destroy-vm"), "--all"])
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
    else:
        sys.exit(0)


class SDWAdminException(Exception):
    pass


if __name__ == "__main__":
    main()
