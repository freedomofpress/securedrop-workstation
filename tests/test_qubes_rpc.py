import functools
import os
import subprocess

import pytest


@functools.cache
def qrexec_policy_graph(service):
    cmd = ["qrexec-policy-graph", "--service", service]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return p.stdout


def policy_exists(source, target, service):
    service_policy_graph = qrexec_policy_graph(service)
    policy_str = f'"{source}" -> "{target}" [label="{service}"'
    return policy_str in service_policy_graph


def test_policy_files_exist():
    """verify the policies are installed"""
    assert os.path.exists("/etc/qubes/policy.d/31-securedrop-workstation.policy")
    assert os.path.exists("/etc/qubes/policy.d/32-securedrop-workstation.policy")


def test_sdlog_from_sdw_to_sdlog_allowed(sdw_tagged_vms):
    """
    All SDW VMs should be permitted to send logs to `sd-log`,
    with the grant applying to all SDW VMs via `@tag:sd-workstation`.
    """
    for vm_name in sdw_tagged_vms:
        if vm_name == "sd-log":
            continue
        assert policy_exists(
            vm_name, "sd-log", "securedrop.Log"
        ), f"Missing for logs from {vm_name} to sd-log"


# securedrop.Log from anything else to sd-log should be denied
def test_sdlog_from_other_to_sdlog_denied(all_vms, sdw_tagged_vms):
    """
    Only SDW VMs should be permitted to send logs to `sd-log`;
    all other VMs on the system should not be able to.
    """
    non_sd_workstation_vms = set(all_vms).difference(set(sdw_tagged_vms))

    for vm in non_sd_workstation_vms:
        if vm.name == "sd-log":
            continue
        assert not policy_exists(
            vm.name, "sd-log", "securedrop.Log"
        ), f"Found unexpected policy for non-SDW {vm.name} to sd-log"


# securedrop.Proxy from sd-app to sd-proxy should be allowed
def test_sdproxy_from_sdapp_to_sdproxy_allowed():
    assert policy_exists("sd-app", "sd-proxy", "securedrop.Proxy")


# securedrop.Proxy from anything else to sd-proxy should be denied
def test_sdproxy_from_other_to_sdproxy_denied():
    assert not policy_exists("sys-net", "sd-proxy", "securedrop.Proxy")
    assert not policy_exists("sys-firewall", "sd-proxy", "securedrop.Proxy")


# qubes.Gpg, qubes.GpgImportKey, and qubes.Gpg2 from anything else to sd-gpg should be denied
def test_qubesgpg_from_other_to_sdgpg_denied():
    assert not policy_exists("sys-net", "sd-gpg", "qubes.Gpg")
    assert not policy_exists("sys-firewall", "sd-gpg", "qubes.Gpg")
    assert not policy_exists("sys-net", "sd-gpg", "qubes.GpgImportKey")
    assert not policy_exists("sys-firewall", "sd-gpg", "qubes.GpgImportKey")
    assert not policy_exists("sys-net", "sd-gpg", "qubes.Gpg2")
    assert not policy_exists("sys-firewall", "sd-gpg", "qubes.Gpg2")
