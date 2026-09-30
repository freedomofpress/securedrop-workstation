#!/usr/bin/env python3

import argparse
import contextlib
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

BUILD_VM = os.environ.get("SECUREDROP_DEV_VM", "sd-dev")
INBOX_TEMPLATE = "sd-inbox-debian-13"
VIEWER_TEMPLATE = "sd-viewer-debian-13"
ADMIN_TEMPLATE = "sd-admin-debian-13"


@dataclass
class Target:
    """A repository to build packages from and the templates to install them into."""

    repo: str
    default_branch: str
    make_target: str
    templates: list[str]
    # Running VMs with this tag are shut down after installing
    tag: str
    # VMs to start after shutdown
    start_vms: list[str]
    done_message: str


CLIENT = Target(
    repo="securedrop-client",
    default_branch="main",
    make_target="build-debs",
    templates=[INBOX_TEMPLATE, VIEWER_TEMPLATE],
    tag="sd-workstation",
    # Manually start sd-proxy so Tor can start up early
    start_vms=["sd-proxy"],
    done_message="You can start the app with `make run-app`.",
)
ADMIN = Target(
    repo="securedrop",
    default_branch="develop",
    make_target="build-debs-admin-notest",
    templates=[ADMIN_TEMPLATE],
    tag="sd-admin",
    start_vms=[],
    done_message="You can now start sd-admin.",
)


def run_in_vm(command: list[str], vmname: str, capture_output: bool = False) -> str | None:
    """Run a command in the build VM."""
    full_command = ["qvm-run", "--pass-io", vmname, " ".join(command)]
    print(f"$ {' '.join(full_command)}")
    if capture_output:
        return subprocess.check_output(full_command, text=True)
    else:
        subprocess.check_call(full_command)
        return None


def check_out_pr(pr_id: int, target: Target) -> None:
    """Check out the PR into the local repository in build VM."""
    print(f"Checking out {target.repo} PR #{pr_id} in {BUILD_VM} VM...")
    branch = f"pr-{pr_id}"
    # first switch to the default branch, removing the PR branch if it exists
    run_in_vm(["git", "-C", target.repo, "checkout", target.default_branch], BUILD_VM)
    with contextlib.suppress(subprocess.CalledProcessError):
        run_in_vm(["git", "-C", target.repo, "branch", "-D", branch], BUILD_VM)
    # Fetch and checkout the PR
    # TODO: this doesn't seem to work with SSH remotes
    run_in_vm(
        ["git", "-C", target.repo, "fetch", "origin", f"pull/{pr_id}/head:{branch}"],
        BUILD_VM,
    )
    run_in_vm(["git", "-C", target.repo, "checkout", branch], BUILD_VM)

    print(f"Successfully checked out PR #{pr_id}")


def build_debs(target: Target) -> None:
    """Run make build-debs (or equivalent) in build VM to build the Debian packages."""
    # TODO: we should download these from CI instead of building them ourselves
    # TODO: an option to also update securedrop-builder?
    print(f"Building Debian packages in {BUILD_VM} VM...")
    run_in_vm(["rm", "-rf", f"{target.repo}/build"], BUILD_VM)
    build_args = ["FAST=1", "make", "-C", target.repo, target.make_target]
    run_in_vm(build_args, BUILD_VM)
    print("Successfully built Debian packages")


def find_debs_in_build_vm(target: Target) -> list[str]:
    """Find all .deb files in the build folder of build VM."""
    print(f"Finding .deb files in {BUILD_VM} VM...")
    # List all .deb files in the build directory
    output = run_in_vm(
        ["find", f"{target.repo}/build", "-name", '"*.deb"'], BUILD_VM, capture_output=True
    )
    assert output is not None  # noqa: S101

    deb_files = [line.strip() for line in output.strip().split("\n") if line.strip()]

    if not deb_files:
        raise RuntimeError("No .deb packages found in the build directory")

    return deb_files


def get_package_name_from_build_vm(deb_path: str) -> str:
    # A bit hacky but should do the job
    return Path(deb_path).name.split("_")[0]


def copy_deb_to_dom0(build_vm_path: str) -> Path:
    """Copy a .deb file from build VM to dom0."""
    # Create a temp file path in dom0
    filename = Path(build_vm_path).name
    dom0_path = Path(tempfile.gettempdir()) / filename

    # Copy from build VM to dom0
    with open(dom0_path, "wb") as f:
        cat_cmd = ["qvm-run", "--pass-io", BUILD_VM, f"cat {build_vm_path}"]
        subprocess.run(cat_cmd, stdout=f, check=True)

    return dom0_path


def move_deb_to_template(dom0_path: Path, template_vm: str) -> str:
    """Move a .deb file from dom0 to template VM."""
    subprocess.check_call(["qvm-move-to-vm", template_vm, str(dom0_path)])
    return f"/home/user/QubesIncoming/dom0/{dom0_path.name}"


def install_debs_in_template(all_deb_paths: list[str], template_vm: str) -> None:
    """Install .deb files in template VM."""

    # Need to escape "${Package}\n" from being interpreted by bash
    dpkg_output = run_in_vm(
        ["dpkg-query", "-f", "\\$\\{Package\\}\\\\n", "--show", "securedrop*"],
        template_vm,
        capture_output=True,
    )
    assert dpkg_output is not None  # noqa: S101
    wanted_packages = dpkg_output.splitlines()
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pr_id", type=int, help="ID of the Pull Request to test")
    parser.add_argument(
        "--admin",
        action="store_true",
        help="Test a securedrop PR by building admin packages and installing them into sd-admin",
    )
    args = parser.parse_args()
    target = ADMIN if args.admin else CLIENT

    print(f"Using build VM: {BUILD_VM}")

    # Run the workflow
    check_out_pr(args.pr_id, target)
    build_debs(target)

    # Find deb files and get their names
    deb_files = find_debs_in_build_vm(target)

    for deb_file in deb_files:
        package_name = get_package_name_from_build_vm(deb_file)
        print(f"Package: {package_name} - {deb_file}")

    # Install the deb files in template VMs
    for template in target.templates:
        install_debs_in_template(deb_files, template)

    # Shutdown
    running_vms = subprocess.check_output(
        ["qvm-ls", "--tags", target.tag, "--raw-list", "--running"], text=True
    ).splitlines()
    subprocess.check_call(["qvm-shutdown", "--wait"] + running_vms)
    for vm in target.start_vms:
        subprocess.check_call(["qvm-start", vm])
    print(f"\n\nYour VMs are provisioned with {target.repo} PR #{args.pr_id}.")
    print(f"\n\n{target.done_message}")


if __name__ == "__main__":
    main()
