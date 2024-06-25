import re
import subprocess
import tempfile
import unittest

from base import SD_VM_Local_Test


class SD_GPG_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-gpg"
        super().setUp()
        # Obtain the fingerprint explicitly configured in dom0 and injected into VMs.
        self.fingerprint = self.dom0_config["submission_key_fpr"]

    def get_dom0_fingerprint(self):
        """
        Obtain the fingerprint of the key actually present in dom0.
        """
        with tempfile.TemporaryDirectory() as d:
            gpg_env = {"GNUPGHOME": d}
            subprocess.check_call(
                ["gpg", "--import", "sd-journalist.sec"],
                env=gpg_env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            local_results = subprocess.check_output(["gpg", "--list-secret-keys"], env=gpg_env)
            return self._extract_fingerprints(local_results)

    def get_vm_fingerprint(self):
        """
        Obtain fingerprints for all keys actually present in GPG VM
        """
        cmd = [
            "qvm-run",
            "-p",
            self.vm_name,
            "/usr/bin/gpg --list-secret-keys",
        ]
        remote_results = subprocess.check_output(cmd)
        return self._extract_fingerprints(remote_results)

    def _extract_fingerprints(self, gpg_output):
        """Helper method to extract fingerprints from GPG command output"""
        return re.findall(r"[A-F0-9]{40}", gpg_output.decode())

    def test_sd_gpg_timeout(self):
        line = "export QUBES_GPG_AUTOACCEPT=28800"
        self.assertFileHasLine("/home/user/.profile", line)

    def test_local_key_in_remote_keyring(self):
        """Verify the key present in dom0 and sd-gpg matches what's configured in config.json"""
        local_fp = self.get_dom0_fingerprint()
        remote_fp = self.get_vm_fingerprint()

        # This also verifies only one secret key is in the keyring
        self.assertEqual(local_fp, [self.fingerprint])
        self.assertEqual(remote_fp, [self.fingerprint])

    def test_logging_disabled(self):
        # Logging to sd-log should be disabled on sd-gpg
        self.assertFalse(self._fileExists("/etc/rsyslog.d/sdlog.conf"))
        self.assertTrue(self._fileExists("/var/run/qubes-service/securedrop-logging-disabled"))


def load_tests(loader, tests, pattern):
    return unittest.TestLoader().loadTestsFromTestCase(SD_GPG_Tests)
