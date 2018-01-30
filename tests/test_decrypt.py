import unittest

from base import SD_VM_Local_Test


class SD_Decrypt_Tests(SD_VM_Local_Test):

    def setUp(self):
        self.vm_name = "sd-decrypt"
        super(SD_Decrypt_Tests, self).setUp()

    def test_decrypt_sd_submission(self):
        self.assertFilesMatch(
          "/usr/local/bin/decrypt-sd-submission",
          "sd-decrypt/decrypt-sd-submission")

    def test_application_x_sd_xfer(self):
        self.assertFilesMatch(
          "/usr/local/share/mime/packages/application-x-sd-xfer.xml",
          "sd-decrypt/application-x-sd-xfer.xml")

    def test_decrypt_sd_submission_desktop(self):
        self.assertFilesMatch(
          "/usr/local/share/applications/decrypt-sd-submission.desktop",
          "sd-decrypt/decrypt-sd-submission.desktop")

    def test_decrypt_sd_user_profile(self):
        self.assertFilesMatch(
          "/home/user/.profile",
          "sd-decrypt/dot-profile")


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Decrypt_Tests)
    return suite
