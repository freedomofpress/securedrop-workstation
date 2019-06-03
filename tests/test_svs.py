import unittest

from base import SD_VM_Local_Test


class SD_SVS_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-svs"
        super(SD_SVS_Tests, self).setUp()

    def test_decrypt_sd_user_profile(self):
        self.assertFilesMatch(
            "/etc/profile.d/sd-svs-qubes-gpg-domain.sh",
            "sd-svs/dot-profile")

    def test_open_in_dvm_desktop(self):
        self.assertFilesMatch(
            "/usr/share/applications/open-in-dvm.desktop",
            "sd-svs/open-in-dvm.desktop")

    def test_mimeapps(self):
        self.assertFilesMatch(
            "/usr/share/applications/mimeapps.list",
            "sd-svs/mimeapps.list")

    def test_sd_client_package_installed(self):
        self.assertTrue(self._package_is_installed("securedrop-client"))


class SD_SVS_Disp_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-svs-disp"
        super(SD_SVS_Disp_Tests, self).setUp()

    def test_sd_client_package_installed(self):
        pkg = "securedrop-workstation-svs-disp"
        self.assertTrue(self._package_is_installed(pkg))

    def test_sd_svs_libreoffice_installed(self):
        self.assertTrue(self._package_is_installed("libreoffice"))


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_SVS_Tests)
    return suite
