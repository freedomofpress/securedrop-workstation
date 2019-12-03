import subprocess
import unittest

STRETCH_TEMPLATES = ["sd-svs-template",
                     "sd-svs-disp-template",
                     "sd-export-template"]


class SD_Qubes_Dom0_Templates_Tests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_Templates_cleaned_up(self):
        cmd = ["qvm-ls", "--raw-list"]
        contents = subprocess.check_output(cmd).decode("utf-8").strip()
        for template in STRETCH_TEMPLATES:
            self.assertTrue(template not in contents)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Qubes_Dom0_Templates_Tests)
    return suite
