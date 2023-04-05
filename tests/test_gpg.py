import re
import subprocess
import unittest
import tempfile

from base import SD_VM_Local_Test


def find_fps_from_gpg_output(gpg):

    fingerprints = []
    lines = gpg.decode("utf-8").split("\n")

    for line in lines:
        regex = r"\s*(Key fingerprint = )?([A-F0-9\s]{50})$"
        m = re.match(regex, line)
        if m:
            fp = m.groups()[1]
            fingerprints.append(fp)

    return fingerprints


def get_local_fp():
    with tempfile.TemporaryDirectory() as d:
        gpg_env = {"GNUPGHOME": d}
        subprocess.check_call(
            ["gpg", "--import", "sd-journalist.sec"],
            env=gpg_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        results = subprocess.check_output(["gpg", "-k", "--with-fingerprint"], env=gpg_env)
        fingerprints = find_fps_from_gpg_output(results)

        # Because we imported this key into a temporary directory,
        # we should only have one key in the keyring.
        if len(fingerprints) == 1:
            return fingerprints[0]


def get_remote_fp(expected_fp):
    cmd = ["qvm-run", "-p", "sd-gpg", "/usr/bin/gpg --list-secret-keys --fingerprint"]

    p = subprocess.check_output(cmd)

    fingerprints = find_fps_from_gpg_output(p)

    # Especially during development, sd-gpg may contain more than one key
    if expected_fp and expected_fp in fingerprints:
        return expected_fp


class SD_GPG_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-gpg"
        super(SD_GPG_Tests, self).setUp()

    def test_sd_gpg_timeout(self):
        line = "export QUBES_GPG_AUTOACCEPT=28800"
        self.assertFileHasLine("/home/user/.profile", line)

    def test_we_have_the_key(self):
        local_fp = get_local_fp()
        remote_fp = get_remote_fp(expected_fp=local_fp)

        self.assertIsNotNone(local_fp, "Local key not found")
        self.assertEqual(local_fp, remote_fp)

    def test_logging_disabled(self):
        # Logging to sd-log should be disabled on sd-gpg
        self.assertFalse(self._fileExists("/etc/rsyslog.d/sdlog.conf"))

    def test_gpg_domain_configured(self):
        self.qubes_gpg_domain_configured(self.vm_name)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_GPG_Tests)
    return suite
