"""
Admin wrapper script for applying salt states for staging and prod scenarios. The rpm
packages only puts the files in place `/srv/salt` but does not apply the state, nor
does it handle the config.
"""

import argparse
import dataclasses
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterator
from contextlib import ContextDecorator, contextmanager
from pathlib import Path
from typing import Literal

from qubesadmin import Qubes
from qubesadmin.vm import QubesVM

from securedrop_manage import (
    CONFIG_FILENAME,
    CONFIG_PATH,
    LEGACY_CONFIG_PATH,
    SUBMISSION_KEY_FILENAME,
    ManageException,
)
from securedrop_manage.configure import import_admin_config, import_journalist_config
from securedrop_manage.products import Product, get_installed_product
from securedrop_manage.validate import AdminConfigValidator, validate_config

# The max concurrency reduction (4->2) was required to avoid "did not return clean data"
# errors from qubesctl. It may be possible to raise this again.
MAX_CONCURRENCY = 2

SALT_PATH = Path("/srv/salt/securedrop_salt/")
ADMIN_SALT_PATH = Path("/srv/salt/admin_salt/")

DEBIAN_VERSION = "13"
BASE_TEMPLATE = f"debian-{DEBIAN_VERSION}-minimal"

# Salt pillar override to make sure dom0 states do not re-enable
# preloaded dispvms. Needed due to inclusion of 'qvm.preload-disposables'
# indirectly via 'qvm.default-dvm'. Removing this does not mean preloaded
# disposables are disabled. Just that they don't get enabled on provisioning.
# FIXME: https://github.com/freedomofpress/securedrop-workstation/issues/1523
PILLAR_DISABLE_PRELOAD = {"qvm": {"dom0": {"preload": False}}}


def parse_args() -> argparse.Namespace:
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
        help=("During uninstall action, don't prompt for confirmation, proceed immediately"),
    )
    parser.add_argument(
        "--configure",
        default=False,
        required=False,
        action="store_true",
        help="Configure SecureDrop Workstation",
    )
    installed_product = get_installed_product()
    if installed_product is Product.ALL:
        # both admin + journalist installed, must explicitly select one or both
        default = None
        choices = [Product.ADMIN, Product.JOURNALIST, Product.ALL]
    else:
        # just one installed, default to it; "all" is accepted as an alias for it
        default = installed_product
        choices = [installed_product, Product.ALL]
    parser.add_argument(
        "--target",
        default=default,
        required=(default is None),
        choices=choices,
        type=Product,
        dest="product",
        help="Whether to operate on the journalist, admin, or both workstations",
    )
    args = parser.parse_args()
    if args.product is Product.ALL:
        # "all" means whatever is installed
        args.product = installed_product
    return args


def move_legacy_config(old_location: Path, new_location: Path) -> None:
    """
    Checks for config files in CONFIG_PATH, and tries to copy them from
    LEGACY_CONFIG_PATH if they're not there.

    This only runs on journalist or combined workstations.
    """
    # make the config directory if it doesn't exist already
    new_location.mkdir(parents=True, exist_ok=True)

    config_files = [CONFIG_FILENAME, SUBMISSION_KEY_FILENAME]
    files_were_copied = False

    for filename in config_files:
        expected_location = new_location / filename
        legacy_location = old_location / filename

        if not expected_location.is_file() and legacy_location.is_file():
            try:
                shutil.copy(legacy_location, expected_location)
                files_were_copied = True
                subprocess.check_call(["sudo", "rm", legacy_location])
            except Exception as e:
                raise ManageException(f"Error moving legacy configuration: {e}")

    if files_were_copied:
        print(
            f"Note: Configuration files were found in the legacy location"
            f" {old_location} and have been moved to {new_location}.\n\n"
        )


def copy_config() -> None:
    """
    Copies config.json and sd-journalist.sec to /srv/salt/securedrop_salt
    """
    try:
        subprocess.check_call(["sudo", "cp", CONFIG_PATH / CONFIG_FILENAME, SALT_PATH])
        subprocess.check_call(["sudo", "cp", CONFIG_PATH / SUBMISSION_KEY_FILENAME, SALT_PATH])
    except subprocess.CalledProcessError:
        raise ManageException("Error copying configuration")


def copy_admin_config() -> None:
    """
    Copies the subset of config.json used by the admin workstation to /srv/salt/admin_salt
    """
    config = AdminConfigValidator(CONFIG_PATH).config
    try:
        subprocess.run(
            ["sudo", "tee", ADMIN_SALT_PATH / "config.json"],
            input=json.dumps(dataclasses.asdict(config)),
            text=True,
            stdout=subprocess.DEVNULL,
            check=True,
        )
    except subprocess.CalledProcessError:
        raise ManageException("Error copying admin configuration")


def pre_provision_journalist() -> None:
    # This is provisioned + configured ahead of time because the kernel needs to be
    # installed, otherwise the descendant templates can't boot
    provision("Provisioning base template", "securedrop_salt.sd-base-template")
    configure("Configuring base template", ["sd-base-debian-13"])


def post_provision_journalist() -> None:
    sync_appmenus("sd-inbox-debian-13")
    sync_appmenus("sd-viewer-debian-13")
    # These are the ones we show in prod VMs, so sync explicitly
    run_cmd(["qvm-sync-appmenus", "--regenerate-only", "sd-devices"])
    run_cmd(["qvm-sync-appmenus", "--regenerate-only", "sd-log"])

    if "sd-fedora-43-dvm" in Qubes().domains:
        # If sd-fedora-43-dvm exists it's because salt determined that sys-usb was disposable
        configure(
            "Add SecureDrop export device handling to sys-usb (disposable)",
            ["sd-fedora-43-dvm"],
            restart=["sys-usb"],
        )
    else:
        configure(
            "Add SecureDrop export device handling to sys-usb (non-disposable)",
            ["sys-usb"],
        )


def post_provision_admin() -> None:
    sync_appmenus("sd-admin-debian-13")


def provision_and_configure(product: Product) -> None:
    """
    Applies the salt state.highstate on dom0 and all VMs
    """

    provision("Provisioning Fedora-based system VMs", "securedrop_shared.sd-sys-vms")

    if product.contains_journalist:
        pre_provision_journalist()

    provision_all()
    configure(
        "Configure all SecureDrop Workstation VMs with service-specific configs",
        [q.name for q in Qubes().domains if "sd-workstation" in q.tags],
    )

    if product.contains_journalist:
        post_provision_journalist()
    if product.contains_admin:
        post_provision_admin()


def run_cmd(args: list[str]) -> None:
    print(f'Running "{" ".join(args)}"')
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError:
        raise ManageException(f"Error while running {' '.join(args)}")


@contextmanager
def suppress_preloaded_disposables() -> Iterator[None]:
    """
    Temporarily disable preloaded disposables during provisioning
    """
    print("[info] Temporarily disabling preloaded disposables")

    # Save current settings
    dom0 = Qubes().domains["dom0"]
    original_preload_dispvm_max = dom0.features.get("preload-dispvm-max", "0")

    # Disable preloaded disposables
    dom0.features["preload-dispvm-max"] = "0"

    try:
        yield
    finally:
        print("[info] Re-enabling preloaded disposables")

        # Reset to original settings
        dom0.features["preload-dispvm-max"] = original_preload_dispvm_max


class template_upgrade_handler(ContextDecorator):
    """
    Temporarily prevents startup of managed qubes

    Necessary during provisioning, particularly in template changes, where
    all qubes dependent on a template (including disposables only
    indirectly based on it) need to be shut down, otherwise provisioning fails.

    NOTE: deferred template changes may make this redundant
    https://github.com/qubesos/qubes-issues/issues/8070
    """

    def __enter__(self) -> Callable[..., ContextDecorator]:
        self.app = Qubes()

        self.skip_upgrade_handler = self.template_upgrades_skipped()
        if self.skip_upgrade_handler:
            return self

        print("[info] Temporarily disabling startup for managed qubes.")
        # Exclude:
        #   - the ones already with prohibit-start for unrelated reasons
        #   - preloaded disposables
        self.excluded = [
            q
            for q in self.app.domains
            if "sd-workstation" in q.tags
            if ("prohibit-start" in q.features or not is_managed(q))
        ]

        affected_qubes = self.affected_qubes()
        for qube in affected_qubes:
            qube.features["prohibit-start"] = "disabled during set up"

        # Use of qvm-shutdown since it can somewhat handle dependencies
        shutdown_list = [q.name for q in affected_qubes]
        if shutdown_list:
            run_cmd(["qvm-shutdown", "--wait", "--"] + shutdown_list)

        return self

    def __exit__(self, *exc: object) -> Literal[False]:
        # No cleanup needed, because it never ran
        if self.skip_upgrade_handler:
            return False

        print("[info] Re-enabling startup for managed qubes.")

        # Obtain the list again since:
        #  - some qubes may have been removed (e.g. old templates)
        #  - some cloned qubes may have inherited prohibit-startup
        for qube in self.affected_qubes():
            if "prohibit-start" in qube.features:
                del qube.features["prohibit-start"]

        return False

    def affected_qubes(self) -> list[QubesVM]:
        # IMPORTANT: List of qubes may have changed
        self.app.domains.refresh_cache(force=True)

        return [
            q
            for q in self.app.domains
            if ("sd-workstation" in q.tags and q not in self.excluded and is_managed(q))
        ]

    def template_upgrades_skipped(self) -> bool:
        # NOTE: a more clever detection is warranted, but inspecting what salt is going
        # to do is not a particular thing salt is good at. This is left here for when
        # re-implemented with another IaC tool that doesn't need wrapper scripts like these.
        templ_current_version_checks = [
            q.features["os-version"] == DEBIAN_VERSION
            for q in Qubes().domains
            if ("sd-workstation" in q.tags and q.klass == "TemplateVM")
        ]

        # Ignore if all templates are using the intended version
        return all(templ_current_version_checks)


def provision(step_description: str, salt_state: str) -> None:
    """
    Create, change or delete qubes
    """
    qubesctl_call(
        step_description,
        ["--", "state.sls", salt_state, f"pillar={json.dumps(PILLAR_DISABLE_PRELOAD)}"],
    )


@template_upgrade_handler()
def provision_all() -> None:
    """
    Provision all enabled salt states
    """
    qubesctl_call(
        "Set up dom0 config files, including RPC policies, and create VMs",
        ["state.highstate", f"pillar={json.dumps(PILLAR_DISABLE_PRELOAD)}"],
    )


def configure(step_description: str, targets: list[str], restart: list[str] = []) -> None:
    """
    Apply configuration to a list of qubes
    """

    # Ignore qubes that are not inteded to be managed directly
    filtered_targets = list(filter(is_managed, targets))
    filtered_restart = list(filter(is_managed, restart))

    qubesctl_call(
        step_description,
        [
            "--skip-dom0",
            "--max-concurrency",
            str(MAX_CONCURRENCY),
            "--targets",
            ",".join(filtered_targets),
            "state.highstate",
        ],
    )

    # Save new configuration to disk by shutting down
    run_cmd(["qvm-shutdown", "--wait", "--"] + filtered_targets)

    if filtered_restart:
        run_cmd(["qvm-shutdown", "--wait", "--"] + filtered_restart)
        run_cmd(["qvm-start", "--"] + filtered_restart)


def qubesctl_call(step_description: str, args: list[str]) -> None:
    qubesctl_cmd = ["sudo", "qubesctl", "--show-output"] + args
    print("\n..........................................................................")
    print(step_description)
    print(f'Running "{" ".join(qubesctl_cmd)}"')

    try:
        subprocess.check_call(qubesctl_cmd)
    except subprocess.CalledProcessError:
        raise ManageException(f"Error in step {step_description}")


def sync_appmenus(vm_name: str) -> None:
    """
    Sync appmenus now that all packages are installed
    TODO: this should be done by salt or debs, but we do it manually here because it's
    not straightforward to run a dom0 salt state after VMs run.
    n.b. none of the sd-inbox-based VMs are shown in the menu on prod,
    but nice to have it synced.
    """
    run_cmd(["qvm-start", "--skip-if-running", vm_name])
    run_cmd(["qvm-sync-appmenus", vm_name])
    run_cmd(["qvm-shutdown", vm_name])


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


def refresh_salt() -> None:
    """
    Cleans the Salt cache and synchronizes Salt to ensure we are applying states
    from the currently installed version
    """
    try:
        subprocess.check_call(["sudo", "rm", "-rf", "/var/cache/salt"])
    except subprocess.CalledProcessError:
        raise ManageException("Error while clearing Salt cache")

    try:
        subprocess.check_call(["sudo", "qubesctl", "saltutil.sync_all", "refresh=true"])
    except subprocess.CalledProcessError:
        raise ManageException("Error while synchronizing Salt")


def destroy_all_tagged(tag: str) -> None:
    """
    Destroys all VMs marked with the specified tag, in the following order:
    DispVMs, AppVMs, then TemplateVMs. Excludes VMs for which
    installed_by_rpm=true.
    """
    sdw_vms = [vm for vm in Qubes().domains if tag in vm.tags]
    sdw_template_vms = [
        vm for vm in sdw_vms if vm.klass == "TemplateVM" and not vm.installed_by_rpm
    ]
    sdw_disp_vms = [vm for vm in sdw_vms if vm.klass == "DispVM"]
    sdw_app_vms = [vm for vm in sdw_vms if vm.klass == "AppVM"]

    # Remove DispVMs first, then AppVMs, then TemplateVMs last.
    for vm in sdw_disp_vms + sdw_app_vms + sdw_template_vms:
        if vm.is_running():
            vm.kill()
        run_cmd(["qvm-remove", "-f", "--", vm.name])


def perform_uninstall(product: Product) -> None:
    packages = []
    if product.contains_admin:
        print("Destroying all admin VMs")
        destroy_all_tagged("sd-admin")
        packages.append("securedrop-admin-dom0-config")

    if product.contains_journalist:
        subprocess.check_call(
            ["sudo", "qubesctl", "state.sls", "securedrop_salt.sd-clean-default-dispvm"]
        )
        print("Destroying all journalist VMs")
        provision("Removing unused SDW qubes", "securedrop_salt.sd-remove-unused-qubes")
        destroy_all_tagged(tag="sd-journalist")
        print("Reverting dom0 configuration")
        subprocess.check_call(["sudo", "qubesctl", "state.sls", "securedrop_salt.sd-clean-all"])
        packages.append("securedrop-workstation-dom0-config")

    print("Uninstalling RPM package(s)")
    subprocess.check_call(["sudo", "dnf", "-y", "-q", "remove", *packages])

    print(
        "Instance secrets (Journalist Interface token and Submission private key) are still "
        f"present on disk. You can delete them in {CONFIG_PATH}"
    )


def is_managed(qube: str | QubesVM) -> bool:
    """
    Help assess if qube is to be managed directly

    Currently excluded qubes:
    - preloaded qubes: they are restarted when changes are
    applied to templates and do no need explicit management.
    """
    if type(qube) is str:
        qube = Qubes().domains[qube]
    return not getattr(qube, "is_preload", False)


def main() -> None:  # noqa: PLR0912
    if os.geteuid() == 0:
        print("Please do not run this script as root.")
        sys.exit(0)

    installed_product = get_installed_product()

    # check for config files under ~/.config/, try to copy them across from
    # the old /usr/share location if they're missing.
    if installed_product.contains_journalist:
        move_legacy_config(LEGACY_CONFIG_PATH, CONFIG_PATH)

    args = parse_args()

    if args.validate:
        print("Validating...", end="")
        validate_config(CONFIG_PATH, args.product)
        print("OK")
    elif args.apply:
        if installed_product is Product.ALL and args.product is not Product.ALL:
            # if we're on a combined workstation, require the use of --all so all VMs
            # are provisioned at the same time
            # FIXME: remove this restriction
            print("--apply can only be used with --target all")
            sys.exit(1)
        if args.product.contains_journalist:
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
        validate_config(CONFIG_PATH, args.product)
        if args.product.contains_journalist:
            copy_config()
        if args.product.contains_admin:
            copy_admin_config()
        refresh_salt()
        with suppress_preloaded_disposables():
            provision_and_configure(args.product)
        print("Provisioning complete. Please reboot to complete the installation.")

    elif args.uninstall:
        print(
            "Uninstalling will remove all packages and destroy all VMs associated\n"
            f"with {args.product.as_text()}."
        )
        if not args.force:
            response = input("Are you sure you want to uninstall (y/N)? ")
            if response.lower() != "y":
                print("Exiting.")
                sys.exit(0)
        refresh_salt()
        perform_uninstall(args.product)
    elif args.configure:
        if args.product.contains_journalist:
            print(
                "Preparing to import SecureDrop Workstation configuration...\n\n"
                "Make sure you have the USB with the submission key and an\n"
                "Admin Workstation or Journalist Workstation USB drive accessible.\n\n\n"
            )
            try:
                validate_config(CONFIG_PATH, Product.JOURNALIST)
                print("Valid configuration found, configuration complete")
            except ManageException:
                import_journalist_config()
        if args.product.contains_admin:
            validate_config(CONFIG_PATH, Product.ADMIN)
            import_admin_config()
    else:
        sys.exit(0)
