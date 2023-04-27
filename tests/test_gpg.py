import re
import subprocess
import unittest
import tempfile

from base import SD_VM_Local_Test


def find_fp_from_gpg_output(gpg):

    lines = gpg.decode("utf-8").split("\n")

    for line in lines:
        # dom0 uses Fedora25 with gpg 1.4.22, whereas AppVMs
        # use Debian9 with gpg 2.1.18, so we'll match fingerprint
        # by a loose regex rather than substring match.
        regex = r"\s*(Key fingerprint = )?([A-F0-9\s]{50})$"
        m = re.match(regex, line)
        if m:
            fp = m.groups()[1]
            return fp


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
        return find_fp_from_gpg_output(results)


def get_remote_fp():
    cmd = ["qvm-run", "-p", "sd-gpg", "/usr/bin/gpg --list-secret-keys --fingerprint"]

    p = subprocess.check_output(cmd)

    return find_fp_from_gpg_output(p)


class SD_GPG_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-gpg"
        super(SD_GPG_Tests, self).setUp()

    def test_sd_gpg_timeout(self):
        line = "export QUBES_GPG_AUTOACCEPT=28800"
        self.assertFileHasLine("/home/user/.profile", line)

    def test_we_have_the_key(self):
        self.assertEqual(get_local_fp(), get_remote_fp())

    def test_logging_disabled(self):
        # Logging to sd-log should be disabled on sd-gpg
        self.assertFalse(self._fileExists("/etc/rsyslog.d/sdlog.conf"))

    def test_gpg_domain_configured(self):
        self.qubes_gpg_domain_configured(self.vm_name)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_GPG_Tests)
    return suite
