import re
import subprocess
import unittest

from base import SD_VM_Local_Test


def find_fp_from_gpg_output(gpg):

    lines = gpg.decode("utf-8").split("\n")

    for line in lines:
        # dom0 uses Fedora25 with gpg 1.4.22, whereas AppVMs
        # use Debian9 with gpg 2.1.18, so we'll match fingerprint
        # by a loose regex rather than substring match.
        regex = '\s*(Key fingerprint = )?([A-F0-9\s]{50})$'
        m = re.match(regex, line)
        if m is not None:
            fp = m.groups()[1]
            return fp


def get_local_fp():

    cmd = ["gpg", "--with-fingerprint", "sd-journalist.sec"]
    p = subprocess.check_output(cmd)

    return find_fp_from_gpg_output(p)


def get_remote_fp():
    cmd = ["qvm-run", "-p", "sd-gpg",
           "/usr/bin/gpg --list-secret-keys --fingerprint"]

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


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_GPG_Tests)
    return suite
