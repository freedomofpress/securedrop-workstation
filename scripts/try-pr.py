#!/usr/bin/env python3

import argparse
import contextlib
import os
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import qubesadmin
import qubesadmin.exc
from qubesadmin.vm import QubesVM

INBOX_TEMPLATE = "sd-inbox-debian-13"
VIEWER_TEMPLATE = "sd-viewer-debian-13"
ADMIN_TEMPLATE = "sd-admin-debian-13"


@dataclass
class Target:
    """A repository to build packages from and the templates to install them into."""

    repo: Path
    default_branch: str
    make_target: str
    templates: list[str]
    # Running VMs with this tag are shut down after installing
    tag: str
    # VMs to start after shutdown
    start_vms: list[str]
    done_message: str


CLIENT = Target(
    repo=Path.home() / "securedrop-client",
    default_branch="main",
    make_target="build-debs",
    templates=[INBOX_TEMPLATE, VIEWER_TEMPLATE],
    tag="sd-workstation",
    # Manually start sd-proxy so Tor can start up early
    start_vms=["sd-proxy"],
    done_message="You can start the app with `make run-app`.",
)
ADMIN = Target(
    repo=Path.home() / "securedrop",
    default_branch="develop",
    make_target="build-debs-admin-notest",
    templates=[ADMIN_TEMPLATE],
    tag="sd-admin",
    start_vms=[],
    done_message="You can now start sd-admin.",
)


def check_requirements(target: Target) -> None:
    """Exit early unless running in the development VM with the dev policy installed."""
    if socket.gethostname() == "dom0":
        sys.exit("This script must now be run from the development VM, not dom0.")
    try:
        app = qubesadmin.Qubes()
        list(app.domains)  # check if admin.vm.List is allowed
        app.domains[target.templates[0]].run("true")
    except (qubesadmin.exc.QubesException, subprocess.CalledProcessError):
        sys.exit(
            "This VM is not allowed to manage SecureDrop qubes. "
            "Run `make dev-vm-policy` in dom0 first."
        )


def check_out_pr(pr_id: int, target: Target) -> None:
    """Check out the PR into the local repository."""
    print(f"Checking out {target.repo} PR #{pr_id}...")
    git = ["git", "-C", str(target.repo)]
    branch = f"pr-{pr_id}"
    # first switch to the default branch, removing the PR branch if it exists
    subprocess.check_call([*git, "checkout", target.default_branch])
    with contextlib.suppress(subprocess.CalledProcessError):
        subprocess.check_call([*git, "branch", "-D", branch])
    # Fetch and checkout the PR
    # TODO: this doesn't seem to work with SSH remotes
    subprocess.check_call([*git, "fetch", "origin", f"pull/{pr_id}/head:{branch}"])
    subprocess.check_call([*git, "checkout", branch])

    print(f"Successfully checked out PR #{pr_id}")


def build_debs(target: Target) -> list[Path]:
    """Run make build-debs (or equivalent) to build the Debian packages."""
    # TODO: we should download these from CI instead of building them ourselves
    # TODO: an option to also update securedrop-builder?
    print("Building Debian packages...")
    subprocess.check_call(["rm", "-rf", str(target.repo / "build")])
    build_args = ["make", "-C", str(target.repo), target.make_target]
    subprocess.check_call(build_args, env={**os.environ, "FAST": "1"})
    print("Successfully built Debian packages")

    debs = sorted((target.repo / "build").rglob("*.deb"))
    if not debs:
        raise RuntimeError("No .deb packages found in the build directory")
    return debs


def install_debs(template: QubesVM, debs: list[Path]) -> None:
    """Install .deb files in template VM."""
    dpkg_output = template.run("dpkg-query -f '${Package}\\n' --show 'securedrop*'")[0]
    wanted_packages = dpkg_output.decode().splitlines()
    print(f"Going to install into {template.name}: {', '.join(wanted_packages)}")

    tmp_dir = template.run("mktemp -d")[0].decode().strip()

    # Copy each deb file to the template
    for deb in debs:
        # A bit hacky but should do the job
        if deb.name.split("_")[0] not in wanted_packages:
            continue
        print(f"Copying {deb.name} to {template.name}...")
        template.run(f"cat > {tmp_dir}/{deb.name}", input=deb.read_bytes())

    # Install all packages in the template
    template.run(
        f"sudo apt-get install --reinstall --yes --allow-downgrades {tmp_dir}/*.deb",
        stdout=None,
        stderr=None,
    )
    print(f"Packages installed successfully in {template.name}")


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

    check_requirements(target)
    app = qubesadmin.Qubes()

    # Run the workflow
    check_out_pr(args.pr_id, target)
    debs = build_debs(target)

    # Install the deb files in template VMs
    for name in target.templates:
        install_debs(app.domains[name], debs)

    # Shutdown
    running_vms = [
        vm
        for vm in app.domains
        if vm.is_running()
        and target.tag in vm.tags
        # Preloaded disposables are restarted by Qubes when their template changes
        and not getattr(vm, "is_preload", False)
    ]
    # Shut down in parallel, like `qvm-shutdown --wait` with several qubes
    with ThreadPoolExecutor() as pool:
        shutdowns = [pool.submit(vm.shutdown, wait=True) for vm in running_vms]
    for shutdown in shutdowns:
        shutdown.result()  # re-raises any shutdown error
    for name in target.start_vms:
        app.domains[name].start()

    print(f"\n\nYour VMs are provisioned with {target.repo} PR #{args.pr_id}.")
    print(f"\n\n{target.done_message}")


if __name__ == "__main__":
    main()
