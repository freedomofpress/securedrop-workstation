import unittest

from qubesadmin import Qubes


SUPPORTED_PLATFORMS = [
        "Fedora 25 (Twenty Five)",
        "Debian GNU/Linux 8 (jessie)",
]


class SD_VM_Platform_Tests(unittest.TestCase):
    def setUp(self):
        self.app = Qubes()

    def tearDown(self):
        pass

    def _get_platform_info(self, vm):
        platform = vm.run("perl -nE '/\"(.*)\"$/ and say $1'")
        return platform

    def test_sd_journalist_template(self):
        vm = self.app.domains["sd-journalist"]
        platform = self._get_platform_info(vm)
        self.assertTrue(platform in SUPPORTED_PLATFORMS)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_VM_Platform_Tests)
    return suite
