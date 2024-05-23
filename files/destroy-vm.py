#!/usr/bin/python3
"""
Utility to quickly destroy a Qubes VM managed by the Workstation
salt config, for use in repeated builds during development.
"""

import argparse
import subprocess
import sys

import qubesadmin

SDW_DEFAULT_TAG = "sd-workstation"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--all",
        default=False,
        required=False,
        action="store_true",
        help="Destroys all SDW VMs",
    )
    parser.add_argument(
        "targets",
        help="List of SDW VMs to destroy",
        nargs=argparse.REMAINDER,
    )
    args = parser.parse_args()
    if not args.all and len(args.targets) < 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    return args


def destroy_vm(vm):
    """
    Destroys a single VM instance. Requires arg to be
    QubesVM object.
    """
    if SDW_DEFAULT_TAG not in vm.tags:
        raise Exception("VM does not have the 'sd-workstation' tag")
    if vm.is_running():
        vm.kill()
    print(f"Destroying VM '{vm.name}'... ", end="")
    subprocess.check_call(["qvm-remove", "-f", vm.name])
    print("OK")


def destroy_all():
    """
    Destroys all VMs marked with the 'sd-workstation' tag, in the following order:
    DispVMs, AppVMs, then TemplateVMs. Excludes VMs for which
    installed_by_rpm=true.
    """
    # Remove DispVMs first, then AppVMs, then TemplateVMs last.
    sdw_vms = [vm for vm in q.domains if SDW_DEFAULT_TAG in vm.tags]
    sdw_template_vms = [
        vm for vm in sdw_vms if vm.klass == "TemplateVM" and not vm.installed_by_rpm
    ]
    sdw_disp_vms = [vm for vm in sdw_vms if vm.klass == "DispVM"]
    sdw_app_vms = [vm for vm in sdw_vms if vm.klass == "AppVM"]

    for vm in sdw_disp_vms:
        destroy_vm(vm)

    for vm in sdw_app_vms:
        destroy_vm(vm)

    for vm in sdw_template_vms:
        destroy_vm(vm)


if __name__ == "__main__":
    args = parse_args()
    q = qubesadmin.Qubes()
    if args.all:
        destroy_all()
    else:
        for t in args.targets:
            vm = q.domains[t]
            destroy_vm(vm)
