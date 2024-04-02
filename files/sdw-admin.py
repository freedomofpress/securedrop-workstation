#!/usr/bin/env python3
"""
Admin wrapper script for applying salt states for staging and prod scenarios. The rpm
packages only puts the files in place `/srv/salt` but does not apply the state, nor
does it handle the config.
"""
import sys
import argparse
import subprocess
import os
import qubesadmin
from typing import List

SCRIPTS_PATH = "/usr/share/securedrop-workstation-dom0-config/"
SALT_PATH = "/srv/salt/sd/"
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
        "--keep-template-rpm",
        default=False,
        required=False,
        action="store_true",
        help="During uninstall action, leave TemplateVM RPM package installed in dom0",
    )
    parser.add_argument(
        "--force",
        default=False,
        required=False,
        action="store_true",
        help="During uninstall action, don't prompt for confirmation, proceed immediately",
    )
    args = parser.parse_args()

    return args


def install_pvh_support():
    """
    Installs grub2-xen-pvh in dom0 - required for PVH with AppVM local kernels
    TODO: install this via package requirements instead if possible
    """
    try:
        subprocess.run(["sudo", "qubes-dom0-update", "-y", "-q", "grub2-xen-pvh"])
    except subprocess.CalledProcessError:
        raise SDWAdminException("Error installing grub2-xen-pvah: local PVH not available.")


def copy_config():
    """
    Copies config.json and sd-journalist.sec to /srv/salt/sd
    """
    try:
        subprocess.check_call(["sudo", "cp", os.path.join(SCRIPTS_PATH, "config.json"), SALT_PATH])
        subprocess.check_call(
            ["sudo", "cp", os.path.join(SCRIPTS_PATH, "sd-journalist.sec"), SALT_PATH]
        )
    except subprocess.CalledProcessError:
        raise SDWAdminException("Error copying configuration")


def provision_all():
    """
    Runs provision-all to apply the salt state.highstate on dom0 and all VMs
    """
    try:
        subprocess.check_call([os.path.join(SCRIPTS_PATH, "scripts/provision-all")])
    except subprocess.CalledProcessError:
        raise SDWAdminException("Error during provision-all")

    print("Provisioning complete. Please reboot to complete the installation.")


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
    app = qubesadmin.Qubes()
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


def perform_uninstall(keep_template_rpm=False):

    try:
        subprocess.check_call(["sudo", "qubesctl", "state.sls", "sd-clean-default-dispvm"])
        print("Destroying all VMs")
        subprocess.check_call([os.path.join(SCRIPTS_PATH, "scripts/destroy-vm"), "--all"])
        print("Reverting dom0 configuration")
        subprocess.check_call(["sudo", "qubesctl", "state.sls", "sd-clean-all"])
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
        provision_all()
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
        perform_uninstall(keep_template_rpm=args.keep_template_rpm)
    else:
        sys.exit(0)


class SDWAdminException(Exception):
    pass


if __name__ == "__main__":
    main()
