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

    def test_sd_export_config_present(self):
        with open("config.json") as c:
            config = json.load(c)

            # Extract values from config.json
            match = re.match(r'sys-usb:(\d)-(\d)', config['usb']['device'])
            pci_bus_id_value = match.group(1)
            usb_device_value = match.group(2)

        wanted_lines = [
            "{",
            "  \"pci_bus_id\": \"{}\",".format(pci_bus_id_value),
            "  \"usb_device\": \"{}\"".format(usb_device_value),
            "}",
        ]
        for line in wanted_lines:
            self.assertFileHasLine("/etc/sd-export-config.json", line)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Export_Tests)
    return suite
