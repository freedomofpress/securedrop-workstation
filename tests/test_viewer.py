import unittest

from base import SD_VM_Local_Test


class SD_Viewer_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-viewer"
        super(SD_Viewer_Tests, self).setUp()

    def test_sd_viewer_config_package_installed(self):
        pkg = "securedrop-workstation-viewer"
        self.assertTrue(self._package_is_installed(pkg))

    def test_sd_viewer_evince_installed(self):
        pkg = "evince"
        self.assertTrue(self._package_is_installed(pkg))

    def test_sd_viewer_libreoffice_installed(self):
        self.assertTrue(self._package_is_installed("libreoffice"))


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Viewer_Tests)
    return suite
