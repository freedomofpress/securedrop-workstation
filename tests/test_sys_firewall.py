import unittest

from base import SD_VM_Local_Test


class SD_Sys_Firewall_Tests(SD_VM_Local_Test):

    def setUp(self):
        self.vm_name = "sys-firewall"
        super(SD_Sys_Firewall_Tests, self).setUp()

    def test_rpm_repo_public_key(self):
        self.assertFilesMatch("/etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation",  # noqa
                              "sd-workstation/apt-test-pubkey.asc")

    def test_rpm_repo_public_key_script(self):
        self.assertFilesMatch("/rw/config/sd-copy-rpm-repo-pubkey.sh",
                              "sys-firewall/sd-copy-rpm-repo-pubkey.sh")


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Sys_Firewall_Tests)
    return suite
