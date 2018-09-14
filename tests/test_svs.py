import unittest

from base import SD_VM_Local_Test


class SD_SVS_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-svs"
        super(SD_SVS_Tests, self).setUp()

    def test_decrypt_sd_submission(self):
        self.assertFilesMatch(
          "/usr/local/bin/decrypt-sd-submission",
          "sd-svs/decrypt-sd-submission")

    def test_decrypt_sd_submission_desktop(self):
        self.assertFilesMatch(
          "/usr/local/share/applications/decrypt-sd-submission.desktop",
          "sd-svs/decrypt-sd-submission.desktop")

    def test_decrypt_sd_user_profile(self):
        self.assertFilesMatch(
          "/home/user/.profile",
          "sd-svs/dot-profile")

    def test_accept_sd_xfer_extracted_file(self):
        self.assertFilesMatch(
            "/usr/local/bin/accept-sd-xfer-extracted",
            "sd-svs/accept-sd-xfer-extracted")

    def test_open_in_dvm_desktop(self):
        self.assertFilesMatch(
          "/usr/local/share/applications/open-in-dvm.desktop",
          "sd-svs/open-in-dvm.desktop")

    def test_mimeapps(self):
        self.assertFilesMatch(
          "/home/user/.config/mimeapps.list",
          "sd-svs/mimeapps.list")


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_SVS_Tests)
    return suite
