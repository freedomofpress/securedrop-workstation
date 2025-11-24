import functools
import os
import subprocess


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


# securedrop.Log from @tag:sd-workstation to sd-log should be allowed
def test_sdlog_from_sdw_to_sdlog_allowed(sdw_tagged_vms):
    for vm in sdw_tagged_vms:
        if vm.name != "sd-log":
            assert policy_exists(vm.name, "sd-log", "securedrop.Log")


# securedrop.Log from anything else to sd-log should be denied
def test_sdlog_from_other_to_sdlog_denied(all_vms, sdw_tagged_vms):
    non_sd_workstation_vms = set(all_vms).difference(set(sdw_tagged_vms))
    for vm in non_sd_workstation_vms:
        if vm.name != "sd-log":
            assert not policy_exists(vm, "sd-log", "securedrop.Log")


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
