import os
import subprocess
import unittest

RETURNCODE_SUCCESS = 0
RETURNCODE_DENIED = 126


class SD_Qubes_Rpc_Tests(unittest.TestCase):
    def _qrexec(self, source_vm, dest_vm, policy_name):
        cmd = ["qvm-run", "--pass-io", source_vm, f"qrexec-client-vm {dest_vm} {policy_name}"]
        p = subprocess.run(cmd, input="test", capture_output=True, text=True, check=False)
        return p.returncode

    def test_policies_exist(self):
        """verify the policies are installed"""
        assert os.path.exists("/etc/qubes/policy.d/31-securedrop-workstation.policy")
        assert os.path.exists("/etc/qubes/policy.d/32-securedrop-workstation.policy")

    # securedrop.Log from @tag:sd-workstation to sd-log should be allowed
    def test_sdlog_from_sdw_to_sdlog_allowed(self):
        self.assertEqual(self._qrexec("sd-app", "sd-log", "securedrop.Log"), RETURNCODE_SUCCESS)

    # securedrop.Log from anything else to sd-log should be denied
    def test_sdlog_from_other_to_sdlog_denied(self):
        self.assertEqual(self._qrexec("sys-net", "sd-log", "securedrop.Log"), RETURNCODE_DENIED)
        self.assertEqual(
            self._qrexec("sys-firewall", "sd-log", "securedrop.Log"), RETURNCODE_DENIED
        )

    # securedrop.Proxy from sd-app to sd-proxy should be allowed
    def test_sdproxy_from_sdapp_to_sdproxy_allowed(self):
        self.assertEqual(self._qrexec("sd-app", "sd-proxy", "securedrop.Proxy"), RETURNCODE_SUCCESS)

    # securedrop.Proxy from anything else to sd-proxy should be denied
    def test_sdproxy_from_other_to_sdproxy_denied(self):
        self.assertEqual(self._qrexec("sys-net", "sd-proxy", "securedrop.Proxy"), RETURNCODE_DENIED)
        self.assertEqual(
            self._qrexec("sys-firewall", "sd-proxy", "securedrop.Proxy"), RETURNCODE_DENIED
        )

    # qubes.Gpg, qubes.GpgImportKey, and qubes.Gpg2 from anything else to sd-gpg should be denied
    def test_qubesgpg_from_other_to_sdgpg_denied(self):
        self.assertEqual(self._qrexec("sys-net", "sd-gpg", "qubes.Gpg"), RETURNCODE_DENIED)
        self.assertEqual(self._qrexec("sys-firewall", "sd-gpg", "qubes.Gpg"), RETURNCODE_DENIED)
        self.assertEqual(self._qrexec("sys-net", "sd-gpg", "qubes.GpgImportKey"), RETURNCODE_DENIED)
        self.assertEqual(
            self._qrexec("sys-firewall", "sd-gpg", "qubes.GpgImportKey"), RETURNCODE_DENIED
        )
        self.assertEqual(self._qrexec("sys-net", "sd-gpg", "qubes.Gpg2"), RETURNCODE_DENIED)
        self.assertEqual(self._qrexec("sys-firewall", "sd-gpg", "qubes.Gpg2"), RETURNCODE_DENIED)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Qubes_Rpc_Tests)
    return suite
