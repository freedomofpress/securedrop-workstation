import os
import subprocess
import unittest

from qubesadmin import Qubes

RETURNCODE_SUCCESS = 0
RETURNCODE_ERROR = 1
RETURNCODE_DENIED = 126


# qrexec-policy-graph
# prints one line with direction that is allowed 
# can filter SOURCE, TARGET, and SERVICE
# not sure if we can filter by tag? but perhaps we can get the VMs by tag


class SD_Qubes_Rpc_Tests(unittest.TestCase):
    # TODO(vicki): use setUpClass to create "state" to store the vms by tag 
    # vms: Set(str)
    # vms_by_tag: Map(str,Set(str)) tag : {vm.name, ...}

    @classmethod 
    def setUpClass(cls):
        cls.all_vms = set()
        cls.vms_by_tag = {}
        app = Qubes() 
        for vm in app.domains:
            if vm.name == "dom0":
                continue
            cls.all_vms.add(vm.name)
            for tag in vm.tags:
                if tag in cls.vms_by_tag:
                    cls.vms_by_tag[tag].append(vm.name)
                else:
                    cls.vms_by_tag[tag] = [vm.name]

    def _qrexec_policy_graph(self, source, target, service):
        cmd = [
            "qrexec-policy-graph",
            "--source",
            source,
            "--target",
            target,
            "--service",
            service
        ]
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return p.stdout

    def _policy_graph_rule_exists(self, source, target, service):
        policy_str = f"\"{source}\" -> \"{target}\" \[label=\"{service}\""
        policy_graph_output = self._qrexec_policy_graph(source, target, service)
        return policy_str in policy_graph_output

    def _qrexec(self, source_vm, dest_vm, policy_name):
        cmd = [
            "qvm-run",
            "--pass-io",
            source_vm,
            f"qrexec-client-vm {dest_vm} {policy_name}",
        ]
        p = subprocess.run(cmd, input="test", capture_output=True, text=True, check=False)
        return p.returncode

    def _get_running_vms_with_and_without_tag(self, tag):
        vms_with_tag = []
        vms_without_tag = []
        app = Qubes()
        for vm in app.domains:
            if vm.name != "dom0" and vm.is_running():
                if tag in list(vm.tags):
                    vms_with_tag.append(vm.name)
                else:
                    vms_without_tag.append(vm.name)
        return vms_with_tag, vms_without_tag

    def test_policies_exist(self):
        """verify the policies are installed"""
        assert os.path.exists("/etc/qubes/policy.d/31-securedrop-workstation.policy")
        assert os.path.exists("/etc/qubes/policy.d/32-securedrop-workstation.policy")

    # securedrop.Log from @tag:sd-workstation to sd-log should be allowed
    def test_sdlog_from_sdw_to_sdlog_allowed(self):
        # vms_with_tag, _ = self._get_running_vms_with_and_without_tag("sd-workstation")
        sd_workstation_vms = self.vms_by_tag["sd-workstation"]
        for vm in sd_workstation_vms:
            if vm != "sd-log":
                self.assertTrue(self._policy_graph_rule_exists(source=vm, target="sd-log", service="securedrop.Log"))

    # securedrop.Log from anything else to sd-log should be denied
    def test_sdlog_from_other_to_sdlog_denied(self):
        vms_without_tag = self.all_vms.difference(self.vms_by_tag["sd-workstation"])
        for vm in vms_without_tag:
            if vm != "sd-log":
                self.assertFalse(self._policy_graph_rule_exists(source=vm, target="sd-log", service="securedrop.Log"))

    # securedrop.Proxy from sd-app to sd-proxy should be allowed
    def test_sdproxy_from_sdapp_to_sdproxy_allowed(self):
        # proxy RPC returns an error due to malformed input, but it still goes through
        # (i.e. not DENIED)
        self.assertEqual(self._qrexec("sd-app", "sd-proxy", "securedrop.Proxy"), RETURNCODE_ERROR)

    # securedrop.Proxy from anything else to sd-proxy should be denied
    def test_sdproxy_from_other_to_sdproxy_denied(self):
        self.assertEqual(self._qrexec("sys-net", "sd-proxy", "securedrop.Proxy"), RETURNCODE_DENIED)
        self.assertEqual(
            self._qrexec("sys-firewall", "sd-proxy", "securedrop.Proxy"),
            RETURNCODE_DENIED,
        )

    # qubes.Gpg, qubes.GpgImportKey, and qubes.Gpg2 from anything else to sd-gpg should be denied
    def test_qubesgpg_from_other_to_sdgpg_denied(self):
        self.assertEqual(self._qrexec("sys-net", "sd-gpg", "qubes.Gpg"), RETURNCODE_DENIED)
        self.assertEqual(self._qrexec("sys-firewall", "sd-gpg", "qubes.Gpg"), RETURNCODE_DENIED)
        self.assertEqual(self._qrexec("sys-net", "sd-gpg", "qubes.GpgImportKey"), RETURNCODE_DENIED)
        self.assertEqual(
            self._qrexec("sys-firewall", "sd-gpg", "qubes.GpgImportKey"),
            RETURNCODE_DENIED,
        )
        self.assertEqual(self._qrexec("sys-net", "sd-gpg", "qubes.Gpg2"), RETURNCODE_DENIED)
        self.assertEqual(self._qrexec("sys-firewall", "sd-gpg", "qubes.Gpg2"), RETURNCODE_DENIED)


def load_tests(loader, tests, pattern):
    return unittest.TestLoader().loadTestsFromTestCase(SD_Qubes_Rpc_Tests)
