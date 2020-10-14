import os
import unittest

from base import SD_VM_Local_Test


class SD_Devices_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-devices-dvm"
        super(SD_Devices_Tests, self).setUp()

    def test_files_are_properly_copied(self):
        self.assertTrue(self._fileExists("/usr/bin/send-to-usb"))
        self.assertTrue(self._fileExists("/usr/share/applications/send-to-usb.desktop"))
        self.assertTrue(self._fileExists("/usr/share/mime/packages/application-x-sd-export.xml"))

    def test_sd_export_package_installed(self):
        self.assertTrue(self._package_is_installed("cryptsetup"))
        self.assertTrue(self._package_is_installed("printer-driver-brlaser"))
        self.assertTrue(self._package_is_installed("securedrop-export"))
        self.assertTrue(self._package_is_installed("gnome-disk-utility"))

    def test_logging_configured(self):
        self.logging_configured()

    def test_mime_types(self):
        filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "vars", "sd-devices.mimeapps"
        )
        with open(filepath, "r") as f:
            lines = f.readlines()
            for line in lines:
                if line != "[Default Applications]\n" and not line.startswith("#"):
                    mime_type = line.split("=")[0]
                    expected_app = line.split("=")[1].split(";")[0]
                    actual_app = self._run("xdg-mime query default {}".format(mime_type))
                    self.assertEqual(actual_app, expected_app)

    def test_open_in_dvm_desktop(self):
        contents = self._get_file_contents("/usr/share/applications/open-in-dvm.desktop")
        expected_contents = [
            "TryExec=/usr/bin/qvm-open-in-vm",
            "Exec=/usr/bin/qvm-open-in-vm --view-only '@dispvm:sd-viewer' %f",
        ]
        for line in expected_contents:
            self.assertTrue(line in contents)

    def test_gpg_domain_configured(self):
        self.qubes_gpg_domain_configured(self.vm_name)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Devices_Tests)
    return suite
