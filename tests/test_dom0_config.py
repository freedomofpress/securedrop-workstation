import subprocess
import unittest

STRETCH_TEMPLATES = [
    "sd-app-template",
    "sd-viewer-template",
    "sd-devices-template",
    "sd-proxy-template",
    "securedrop-workstation"
]

VMS_TO_UPDATE = [
    "sd-app-buster-template",
    "sd-viewer-buster-template",
    "sd-proxy-buster-template",
    "sd-devices-buster-template",
    "whonix-ws-15",
    "whonix-gw-15",
    "securedrop-workstation-buster"
]


class SD_Qubes_Dom0_Templates_Tests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_Templates_cleaned_up(self):
        cmd = ["qvm-ls", "--raw-list"]
        contents = subprocess.check_output(cmd).decode("utf-8").split()
        for template in STRETCH_TEMPLATES:
            for line in contents:
                self.assertFalse(template == line)

    def test_vms_to_update_are_tagged(self):
        cmd = ["qvm-ls",
               "--tags", "sd-workstation-updates",
               "--raw-data",
               "--fields", "NAME"]
        contents = subprocess.check_output(cmd).decode("utf-8").strip()
        for template in VMS_TO_UPDATE:
            self.assertTrue(template in contents)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Qubes_Dom0_Templates_Tests)
    return suite
