#!/usr/bin/env python3

import argparse
import contextlib
import os
import subprocess
import tempfile
from pathlib import Path

BUILD_VM = os.environ.get("SECUREDROP_DEV_VM", "sd-dev")
SMALL_TEMPLATE = "sd-small-bookworm-template"
LARGE_TEMPLATE = "sd-large-bookworm-template"


def run_in_vm(command, vmname, capture_output=False):
    """Run a command in the build VM."""
    full_command = ["qvm-run", "--pass-io", vmname, " ".join(command)]
    print(f"$ {' '.join(full_command)}")
    if capture_output:
        return subprocess.check_output(full_command, text=True)
    else:
        subprocess.check_call(full_command)
        return None


def check_out_pr(pr_id):
    """Check out the PR into the local repository in build VM."""
    print(f"Checking out PR #{pr_id} in {BUILD_VM} VM...")
    branch = f"pr-{pr_id}"
    # first switch to main, removing the PR branch if it exists
    run_in_vm(["git", "-C", "securedrop-client", "checkout", "main"], BUILD_VM)
    with contextlib.suppress(subprocess.CalledProcessError):
        run_in_vm(["git", "-C", "securedrop-client", "branch", "-D", branch], BUILD_VM)
    # Fetch and checkout the PR
    # TODO: this doesn't seem to work with SSH remotes
    run_in_vm(
        ["git", "-C", "securedrop-client", "fetch", "origin", f"pull/{pr_id}/head:{branch}"],
        BUILD_VM,
    )
    run_in_vm(["git", "-C", "securedrop-client", "checkout", branch], BUILD_VM)

    print(f"Successfully checked out PR #{pr_id}")


def build_debs(build_app: bool):
    """Run make build-debs in build VM to build the Debian packages."""
    # TODO: we should download these from CI instead of building them ourselves
    # TODO: an option to also update securedrop-builder?
    print(f"Building Debian packages in {BUILD_VM} VM...")
    run_in_vm(["rm", "-rf", "securedrop-client/build"], BUILD_VM)
    build_args = ["FAST=1"]
    if build_app:
        build_args.append("WHAT=app")
    build_args.extend(["make", "-C", "securedrop-client", "build-debs"])
    run_in_vm(build_args, BUILD_VM)
    print("Successfully built Debian packages")


def find_debs_in_build_vm():
    """Find all .deb files in the build folder of build VM."""
    print(f"Finding .deb files in {BUILD_VM} VM...")
    # List all .deb files in the build directory
    output = run_in_vm(
        ["find", "securedrop-client/build", "-name", '"*.deb"'], BUILD_VM, capture_output=True
    )

    deb_files = [line.strip() for line in output.strip().split("\n") if line.strip()]

    if not deb_files:
        raise RuntimeError("No .deb packages found in the build directory")

    return deb_files


def get_package_name_from_build_vm(deb_path: str) -> str:
    # A bit hacky but should do the job
    return Path(deb_path).name.split("_")[0]


def copy_deb_to_dom0(build_vm_path):
    """Copy a .deb file from build VM to dom0."""
    # Create a temp file path in dom0
    filename = Path(build_vm_path).name
    dom0_path = Path(tempfile.gettempdir()) / filename

    # Copy from build VM to dom0
    with open(dom0_path, "wb") as f:
        cat_cmd = ["qvm-run", "--pass-io", BUILD_VM, f"cat {build_vm_path}"]
        subprocess.run(cat_cmd, stdout=f, check=True)

    return dom0_path


def move_deb_to_template(dom0_path, template_vm):
    """Move a .deb file from dom0 to template VM."""
    subprocess.check_call(["qvm-move-to-vm", template_vm, str(dom0_path)])
    return f"/home/user/QubesIncoming/dom0/{dom0_path.name}"


def install_debs_in_template(all_deb_paths, template_vm, build_app: bool):
    """Install .deb files in template VM."""

    # Need to escape "${Package}\n" from being interpreted by bash
    wanted_packages = run_in_vm(
        ["dpkg-query", "-f", "\\$\\{Package\\}\\\\n", "--show", "securedrop*"],
        template_vm,
        capture_output=True,
    ).splitlines()
    if build_app and "securedrop-client" in wanted_packages:
        # If this is the VM where the client is installed, also install the app
        wanted_packages.append("securedrop-app")
    print(f"Going to install into {template_vm}: {', '.join(wanted_packages)}")

    template_deb_paths = []

    # Copy each deb file to the template
    for build_vm_path in all_deb_paths:
        if get_package_name_from_build_vm(build_vm_path) not in wanted_packages:
            continue
        print(f"Copying {Path(build_vm_path).name} to {template_vm}...")
        dom0_path = copy_deb_to_dom0(build_vm_path)
        template_path = move_deb_to_template(dom0_path, template_vm)
        template_deb_paths.append(str(template_path))

    # Install all packages in the template
    debs_list = " ".join(template_deb_paths)
    run_in_vm(
        ["sudo", "apt-get", "install", "--reinstall", "--yes", "--allow-downgrades", debs_list],
        template_vm,
    )
    print(f"Packages installed successfully in {template_vm}; cleaning up")
    run_in_vm(["rm", "-v", debs_list], template_vm)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pr_id", type=int, help="ID of the Pull Request to test")
    parser.add_argument(
        "--app", default=False, action="store_true", help="Build and install SecureDrop App too"
    )
    args = parser.parse_args()

    print(f"Using build VM: {BUILD_VM}")

    # Run the workflow
    check_out_pr(args.pr_id)
    build_debs(build_app=args.app)

    # Find deb files and get their names
    deb_files = find_debs_in_build_vm()

    for deb_file in deb_files:
        package_name = get_package_name_from_build_vm(deb_file)
        print(f"Package: {package_name} - {deb_file}")

    # Install the deb files in template VMs
    install_debs_in_template(deb_files, SMALL_TEMPLATE, build_app=args.app)
    install_debs_in_template(deb_files, LARGE_TEMPLATE, build_app=args.app)

    # Shutdown
    all_vms = subprocess.check_output(
        ["qvm-ls", "--tags", "sd-workstation", "--raw-list", "--running"]
    ).splitlines()
    subprocess.check_call(["qvm-shutdown", "--wait"] + all_vms)
    # Manually start sd-proxy so Tor can start up early
    subprocess.check_call(["qvm-start", "sd-proxy"])
    print(f"\n\nYour workstation is provisioned with PR #{args.pr_id}.")
    target = "app" if args.app else "client"
    print(f"\n\nYou can start the {target} with `make run-{target}`.")


if __name__ == "__main__":
    main()
