import json
import re
import unittest

from base import SD_VM_Local_Test


class SD_Export_Tests(SD_VM_Local_Test):

    def setUp(self):
        self.vm_name = "sd-export-usb-dvm"
        super(SD_Export_Tests, self).setUp()

    def test_files_are_properly_copied(self):
        self.assertTrue(self._fileExists("/usr/bin/send-to-usb"))
        self.assertTrue(self._fileExists("/usr/share/applications/send-to-usb.desktop"))
        self.assertTrue(self._fileExists("/usr/share/mime/packages/application-x-sd-export.xml"))

    def test_sd_export_package_installed(self):
        self.assertTrue(self._package_is_installed("cryptsetup"))
        self.assertTrue(self._package_is_installed("printer-driver-brlaser"))
        self.assertTrue(self._package_is_installed("securedrop-export"))


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Export_Tests)
    return suite
