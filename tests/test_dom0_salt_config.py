import subprocess
import unittest


class SD_Dom0_Salt_Config_Tests(unittest.TestCase):
    def setUp(self):
        # Enable full diff output in test report, to aid in debugging
        self.maxDiff = None

    def test_is_topfile_enabled(self):
        cmd = ["sudo", "qubesctl", "top.enabled"]
        wanted = "securedrop_salt.sd-workstation.top"

        try:
            all_topfiles = subprocess.check_output(cmd).decode("utf-8")
            assert wanted in all_topfiles

        except subprocess.CalledProcessError:
            self.fail("Error checking topfiles")


def load_tests(loader, tests, pattern):
    return unittest.TestLoader().loadTestsFromTestCase(SD_Dom0_Salt_Config_Tests)
