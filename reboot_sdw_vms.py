#!/usr/bin/env python3
import json
import logging
import os
import subprocess


sdlog = logging.getLogger(__name__)


def shutdown_and_start_vms():
    """
    Power cycles the vms to ensure. we should do them all in one shot to reduce complexity
    and likelihood of failure. Rebooting the VMs will ensure the TemplateVM
    updates are picked up by the AppVM. We must first shut all VMs down to ensure
    correct order of operations, as sd-whonix cannot shutdown if sd-proxy is powered
    on, for example.

    System AppVMs(sys-net, sys-firewall and sys-usb) will need to be killed and restarted
    in case they are being used by another non-workstation VM.
    """

    sdw_vms_in_order = [
        "sys-whonix",
        "sd-proxy",
        "sd-whonix",
        "sd-app",
        "sd-gpg",
        "sd-log",
    ]
    sdlog.info("Shutting down SDW VMs for updates")
    for vm in sdw_vms_in_order:
        _safely_shutdown_vm(vm)

    sys_vms_in_order = ["sys-firewall", "sys-net", "sys-usb"]
    sdlog.info("Killing system fedora-based VMs for updates")
    for vm in sys_vms_in_order:
        try:
            subprocess.check_output(["qvm-kill", vm], stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            sdlog.error("Error while killing {}".format(vm))
            sdlog.error(str(e))
            sdlog.error(str(e.stderr))

    sdlog.info("Starting system fedora-based VMs after updates")
    for vm in reversed(sys_vms_in_order):
        _safely_start_vm(vm)

    sdlog.info("Starting SDW VMs after updates")
    for vm in reversed(sdw_vms_in_order):
        _safely_start_vm(vm)


def _safely_shutdown_vm(vm):
    try:
        subprocess.check_output(["qvm-shutdown", "--wait", vm],
                                stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        sdlog.error("Failed to shut down {}".format(vm))
        sdlog.error(str(e))
        sdlog.error(str(e.stderr))
        return UpdateStatus.UPDATES_FAILED


def _safely_start_vm(vm):
    try:
        running_vms = subprocess.check_output(["xl", "list"],
                                stderr=subprocess.PIPE)
        sdlog.info("xl list before starting VM: {}".format(running_vms))
        subprocess.check_output(["qvm-start", "--skip-if-running", vm],
                                stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        sdlog.error("Error while starting {}".format(vm))
        sdlog.error(str(e))
        sdlog.error(str(e.stderr))


