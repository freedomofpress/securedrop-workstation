import re
import subprocess
import tempfile
import unittest

from base import SD_VM_Local_Test


class SD_GPG_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-gpg"
        super().setUp()

    def getLocalFingerprint(self):
        """
        Obtain fingerprint for the key configured in dom0
        """
        with tempfile.TemporaryDirectory() as d:
            gpg_env = {"GNUPGHOME": d}
            subprocess.check_call(
                ["gpg", "--import", "sd-journalist.sec"],
                env=gpg_env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            local_results = subprocess.check_output(
                ["gpg", "-k", "--with-fingerprint"], env=gpg_env
            )
            return self._extract_fingerprints(local_results)

    def getRemoteFingerprints(self):
        """
        Obtain fingerprints for all keys configured in GPG VM
        """
        cmd = [
            "qvm-run",
            "-p",
            self.vm_name,
            "/usr/bin/gpg --list-secret-keys --fingerprint",
        ]
        remote_results = subprocess.check_output(cmd)
        return self._extract_fingerprints(remote_results)

    def _extract_fingerprints(self, gpg_output):
        """Helper method to extract fingerprints from GPG command output"""
        fingerprints = []
        lines = gpg_output.decode("utf-8").split("\n")

        for line in lines:
            regex = r"\s*(Key fingerprint = )?([A-F0-9\s]{50})$"
            m = re.match(regex, line)
            if m:
                fp = m.groups()[1]
                fingerprints.append(fp)

        return fingerprints

    def test_sd_gpg_timeout(self):
        line = "export QUBES_GPG_AUTOACCEPT=28800"
        self.assertFileHasLine("/home/user/.profile", line)

    def test_local_key_in_remote_keyring(self):
        # Get fingerprints from dom0 filesystem (sd-journalist.sec) and GPG VM keyring
        local_fp = self.getLocalFingerprint()
        remote_fp = self.getRemoteFingerprints()

        # Exactly one fingerprint extracted from sd-journalist.sec
        self.assertEqual(len(local_fp), 1)

        # Local fingerprint is not falsy (e.g., "", None)
        self.assertTrue(local_fp[0])

        # At least one key in GPG VM keyring
        self.assertGreater(len(remote_fp), 0)

        # Local key in GPG VM keyring
        self.assertIn(local_fp[0], remote_fp)

    def test_logging_disabled(self):
        # Logging to sd-log should be disabled on sd-gpg
        self.assertFalse(self._fileExists("/etc/rsyslog.d/sdlog.conf"))
        self.assertTrue(self._fileExists("/var/run/qubes-service/securedrop-logging-disabled"))


def load_tests(loader, tests, pattern):
    return unittest.TestLoader().loadTestsFromTestCase(SD_GPG_Tests)
