import functools
import os
import subprocess
from datetime import datetime

import pytest
import systemd.journal  # Available in dom0 by default
from qubesadmin import Qubes

from tests.base import SD_TAG, is_managed_qube


@functools.cache
def qrexec_policy_graph(service):
    cmd = ["qrexec-policy-graph", "--service", service]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return p.stdout


@pytest.mark.provisioning
def policy_exists(source, target, service):
    service_policy_graph = qrexec_policy_graph(service)
    policy_str = f'"{source}" -> "{target}" [label="{service}"'
    return policy_str in service_policy_graph


@pytest.mark.provisioning
def test_policy_files_exist():
    """verify the policies are installed"""
    assert os.path.exists("/etc/qubes/policy.d/31-securedrop-workstation.policy")
    assert os.path.exists("/etc/qubes/policy.d/32-securedrop-workstation.policy")


@pytest.mark.provisioning
def test_sdlog_from_sdw_to_sdlog_allowed(sdw_tagged_vms):
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
def test_sdlog_from_other_to_sdlog_denied(all_vms, sdw_tagged_vms):
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
def test_sdproxy_from_sdapp_to_sdproxy_allowed():
    assert policy_exists("sd-app", "sd-proxy", "securedrop.Proxy")


# securedrop.Proxy from anything else to sd-proxy should be denied
@pytest.mark.provisioning
def test_sdproxy_from_other_to_sdproxy_denied():
    assert not policy_exists("sys-net", "sd-proxy", "securedrop.Proxy")
    assert not policy_exists("sys-firewall", "sd-proxy", "securedrop.Proxy")


# qubes.Gpg, qubes.GpgImportKey, and qubes.Gpg2 from anything else to sd-gpg should be denied
@pytest.mark.provisioning
def test_qubesgpg_from_other_to_sdgpg_denied():
    assert not policy_exists("sys-net", "sd-gpg", "qubes.Gpg")
    assert not policy_exists("sys-firewall", "sd-gpg", "qubes.Gpg")
    assert not policy_exists("sys-net", "sd-gpg", "qubes.GpgImportKey")
    assert not policy_exists("sys-firewall", "sd-gpg", "qubes.GpgImportKey")
    assert not policy_exists("sys-net", "sd-gpg", "qubes.Gpg2")
    assert not policy_exists("sys-firewall", "sd-gpg", "qubes.Gpg2")


class Test_Dom0_RPC_GetJournalistSecretkeys:
    def test_rpc_success(self, dom0_config):
        """
        Make sure RPC service obtains a private GPG key

        NOTE: Functional GPG part is in sd-gpg tests.
        """

        cmd = ["/etc/qubes-rpc/securedrop.GetJournalistSecretKeys"]
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert p.returncode == 0
        assert "-----BEGIN PGP PRIVATE KEY BLOCK-----" in p.stdout

    def test_rpc_failure(self, tmpdir):
        # Start watching the systemd journal to catch the error message
        journal = systemd.journal.Reader()
        journal.add_match(SYSLOG_IDENTIFIER="securedrop.GetJournalistSecretKeys")
        journal.seek_realtime(datetime.now())

        # Force a failure by overriding the expected key location
        non_existent_key = tmpdir / "non-existent-key.sec"
        with pytest.raises(subprocess.CalledProcessError):
            subprocess.run(
                ["/etc/qubes-rpc/securedrop.GetJournalistSecretKeys"],
                env={"MAIN_SECRET_KEY_PATH": non_existent_key},
                check=True,
            )

        # Check error message in system journal
        journal_entries = map(lambda e: e.get("MESSAGE"), journal)
        assert f"Error: Secret keys file not found: {non_existent_key}" in journal_entries

    # securedrop.GetJournalistSecretKeys only allowed in: sd-gpg -> dom0
    @pytest.mark.parametrize(
        "src_qube_name",
        [vm.name for vm in Qubes().domains if SD_TAG in vm.tags],
    )
    @pytest.mark.provisioning
    def test_policy_from_sdgpg_to_dom0_allowed(self, src_qube_name):
        allowed = policy_exists(src_qube_name, "@adminvm", "securedrop.GetJournalistSecretKeys")

        if src_qube_name == "sd-gpg":
            assert allowed
        else:
            assert not allowed
