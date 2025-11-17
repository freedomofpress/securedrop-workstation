import functools
import os
import subprocess


class SD_Qubes_Rpc_Tests:
    @functools.cache
    def _qrexec_policy_graph(self, service):
        cmd = ["qrexec-policy-graph", "--service", service]
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return p.stdout

    def _policy_exists(self, source, target, service):
        service_policy_graph = self._qrexec_policy_graph(service)
        policy_str = f'"{source}" -> "{target}" [label="{service}"'
        return policy_str in service_policy_graph

    def test_policy_files_exist(self):
        """verify the policies are installed"""
        assert os.path.exists("/etc/qubes/policy.d/31-securedrop-workstation.policy")
        assert os.path.exists("/etc/qubes/policy.d/32-securedrop-workstation.policy")

    # securedrop.Log from @tag:sd-workstation to sd-log should be allowed
    def test_sdlog_from_sdw_to_sdlog_allowed(self, sdw_tagged_vms):
        for vm in sdw_tagged_vms:
            if vm != "sd-log":
                assert self._policy_exists(vm, "sd-log", "securedrop.Log")

    # securedrop.Log from anything else to sd-log should be denied
    def test_sdlog_from_other_to_sdlog_denied(self, all_vms, sdw_tagged_vms):
        non_sd_workstation_vms = set(all_vms).difference(set(sdw_tagged_vms))
        for vm in non_sd_workstation_vms:
            if vm != "sd-log":
                assert not self._policy_exists(vm, "sd-log", "securedrop.Log")

    # securedrop.Proxy from sd-app to sd-proxy should be allowed
    def test_sdproxy_from_sdapp_to_sdproxy_allowed(self):
        assert self._policy_exists("sd-app", "sd-proxy", "securedrop.Proxy")

    # securedrop.Proxy from anything else to sd-proxy should be denied
    def test_sdproxy_from_other_to_sdproxy_denied(self):
        assert not self._policy_exists("sys-net", "sd-proxy", "securedrop.Proxy")
        assert not self._policy_exists("sys-firewall", "sd-proxy", "securedrop.Proxy")

    # qubes.Gpg, qubes.GpgImportKey, and qubes.Gpg2 from anything else to sd-gpg should be denied
    def test_qubesgpg_from_other_to_sdgpg_denied(self):
        assert not self._policy_exists("sys-net", "sd-gpg", "qubes.Gpg")
        assert not self._policy_exists("sys-firewall", "sd-gpg", "qubes.Gpg")
        assert not self._policy_exists("sys-net", "sd-gpg", "qubes.GpgImportKey")
        assert not self._policy_exists("sys-firewall", "sd-gpg", "qubes.GpgImportKey")
        assert not self._policy_exists("sys-net", "sd-gpg", "qubes.Gpg2")
        assert not self._policy_exists("sys-firewall", "sd-gpg", "qubes.Gpg2")
