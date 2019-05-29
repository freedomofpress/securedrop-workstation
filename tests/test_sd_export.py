import unittest

from base import SD_VM_Local_Test


class SD_Export_Tests(SD_VM_Local_Test):

    def setUp(self):
        self.vm_name = "sd-export-usb-dvm"
        super(SD_Export_Tests, self).setUp()

    def test_files_are_properly_copied(self):
        self.assertFilesMatch("/usr/bin/send-to-usb",
                              "sd-export/send-to-usb")
        self.assertFilesMatch("/usr/share/applications/send-to-usb.desktop",
                              "sd-export/send-to-usb.desktop")
        self.assertFilesMatch("/usr/share/mime/packages/application-x-sd-export.xml", # noqa
                              "sd-export/application-x-sd-export.xml")


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Export_Tests)
    return suite
