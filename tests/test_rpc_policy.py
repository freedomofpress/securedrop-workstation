import functools
import os
import subprocess

import pytest
from qubesadmin.app import VMCollection
from qubesadmin.vm import QubesVM

from tests.base import is_managed_qube


@functools.cache
def qrexec_policy_graph(service: str) -> str:
    cmd = ["qrexec-policy-graph", "--service", service]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return p.stdout


@pytest.mark.provisioning
def policy_exists(source: str, target: str, service: str) -> bool:
    service_policy_graph = qrexec_policy_graph(service)
    policy_str = f'"{source}" -> "{target}" [label="{service}"'
    return policy_str in service_policy_graph


@pytest.mark.provisioning
def test_policy_files_exist() -> None:
    """verify the policies are installed"""
    assert os.path.exists("/etc/qubes/policy.d/31-securedrop-workstation.policy")
    assert os.path.exists("/etc/qubes/policy.d/32-securedrop-workstation.policy")


@pytest.mark.provisioning
def test_sdlog_from_sdw_to_sdlog_allowed(sdw_tagged_vms: list[QubesVM]) -> None:
    """
    All SDW VMs should be permitted to send logs to `sd-log`,
    with the grant applying to all SDW VMs via `@tag:sd-workstation`.
    """
    for vm in sdw_tagged_vms:
        if vm.name == "sd-log":
            continue
        assert policy_exists(
            vm.name, "sd-log", "securedrop.Log"
        ), f"Missing for logs from {vm} to sd-log"


# securedrop.Log from anything else to sd-log should be denied
@pytest.mark.provisioning
def test_sdlog_from_other_to_sdlog_denied(
    all_vms: VMCollection, sdw_tagged_vms: list[QubesVM]
) -> None:
    """
    Only SDW VMs should be permitted to send logs to `sd-log`;
    all other VMs on the system should not be able to.
    """

    # Filter out preloaded disposables and side-effects from other tests
    all_vms_set = set(
        [vm for vm in all_vms if vm.name != "sd-viewer-disposable" and is_managed_qube(vm)]
    )
    non_sd_workstation_vms = all_vms_set.difference(set(sdw_tagged_vms))
    for vm in non_sd_workstation_vms:
        if vm.name == "sd-log":
            continue
        assert not policy_exists(
            vm.name, "sd-log", "securedrop.Log"
        ), f"Found unexpected policy for non-SDW {vm.name} to sd-log"


# securedrop.Proxy from sd-app to sd-proxy should be allowed
@pytest.mark.provisioning
def test_sdproxy_from_sdapp_to_sdproxy_allowed() -> None:
    assert policy_exists("sd-app", "sd-proxy", "securedrop.Proxy")


# securedrop.Proxy from anything else to sd-proxy should be denied
@pytest.mark.provisioning
def test_sdproxy_from_other_to_sdproxy_denied() -> None:
    assert not policy_exists("sys-net", "sd-proxy", "securedrop.Proxy")
    assert not policy_exists("sys-firewall", "sd-proxy", "securedrop.Proxy")


# qubes.Gpg, qubes.GpgImportKey, and qubes.Gpg2 from anything else to sd-gpg should be denied
@pytest.mark.provisioning
def test_qubesgpg_from_other_to_sdgpg_denied() -> None:
    assert not policy_exists("sys-net", "sd-gpg", "qubes.Gpg")
    assert not policy_exists("sys-firewall", "sd-gpg", "qubes.Gpg")
    assert not policy_exists("sys-net", "sd-gpg", "qubes.GpgImportKey")
    assert not policy_exists("sys-firewall", "sd-gpg", "qubes.GpgImportKey")
    assert not policy_exists("sys-net", "sd-gpg", "qubes.Gpg2")
    assert not policy_exists("sys-firewall", "sd-gpg", "qubes.Gpg2")


@pytest.mark.provisioning
def test_policy_from_sdgpg_to_dom0_allowed(sdw_tagged_vms: list[QubesVM], qubes_ver: str) -> None:
    """Securedrop.GetSecretKeys only allowed in: sd-gpg -> dom0"""

    for qube in sdw_tagged_vms:
        allowed = policy_exists(qube.name, "dom0", "securedrop.GetSecretKeys")
        if qube.name == "sd-gpg":
            assert allowed
        else:
            assert not allowed


@pytest.mark.provisioning
def test_usbattach_policy_denies_sd_workstation(sdw_tagged_vms: list[QubesVM]) -> None:
    """
    Regression test: qubes.USBAttach to or from any @tag:sd-workstation VM must
    be denied and must NOT resolve to an 'ask' prompt.

    Previously, the wildcard 'qubes.USBAttach * @anyvm @anyvm ask' rule in
    31-securedrop-workstation.policy was evaluated before the deny rules in
    32-securedrop-workstation.policy (first-match-wins), making the deny rules
    unreachable dead code. The fix adds explicit deny rules for @tag:sd-workstation
    directly in file 31, before the wildcard ask rule.
    """
    # Representative non-SDW VMs that should not be able to attach USB to an
    # sd-workstation-tagged VM (or have USB attached from one).
    non_sdw_sources = ["sys-net", "sys-firewall", "sys-usb"]

    for vm in sdw_tagged_vms:
        # Skip sd-export-target VMs: sys-usb -> @tag:sd-export-target is
        # intentionally allowed via an explicit allow rule above the deny rules.
        if "sd-export-target" in vm.tags:
            continue

        for non_sdw_qube in non_sdw_sources:
            # No external VM should be able to attach USB to an sd-workstation VM.
            assert not policy_exists(
                non_sdw_qube, vm.name, "qubes.USBAttach"
            ), (
                f"qubes.USBAttach from {non_sdw_qube} to {vm.name} should be denied, "
                f"but a policy route was found. The @anyvm @anyvm ask wildcard in "
                f"31-securedrop-workstation.policy may be shadowing the deny rule."
            )

            # No sd-workstation VM should be able to initiate a USB attach to
            # an external VM either.
            assert not policy_exists(
                vm.name, non_sdw_qube, "qubes.USBAttach"
            ), (
                f"qubes.USBAttach from {vm.name} to {non_sdw_qube} should be denied, "
                f"but a policy route was found."
            )
