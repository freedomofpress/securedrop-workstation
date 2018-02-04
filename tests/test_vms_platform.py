import unittest

from qubesadmin import Qubes


SUPPORTED_PLATFORMS = [
    "Fedora 26 (Twenty Six)",
    "Debian GNU/Linux 8 (jessie)",
]

WANTED_VMS = [
    "sd-decrypt",
    "sd-gpg",
    "sd-journalist",
    "sd-svs",
    "sd-svs-disp",
    "sd-whonix",
]


class SD_VM_Platform_Tests(unittest.TestCase):
    def setUp(self):
        self.app = Qubes()

    def tearDown(self):
        pass

    def _get_platform_info(self, vm):
        cmd = "perl -nE '/^PRETTY_NAME=\"(.*)\"$/ and say $1' /etc/os-release"
        stdout, stderr = vm.run(cmd)
        platform = stdout.rstrip("\n")
        return platform

    def _validate_vm_platform(self, vm):
        platform = self._get_platform_info(vm)
        self.assertIn(platform, SUPPORTED_PLATFORMS)

    def test_sd_journalist_template(self):
        vm = self.app.domains["sd-journalist"]
        self._validate_vm_platform(vm)

    def test_all_sd_vm_platforms(self):
        """
        Test all VM platforms iteratively.
        """
        # Would prefer to use a feature like pytest.mark.parametrize
        # for better error output here, but not available in dom0.
        for vm_name in WANTED_VMS:
            vm = self.app.domains[vm_name]
            self._validate_vm_platform(vm)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_VM_Platform_Tests)
    return suite
