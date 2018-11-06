import unittest

from base import SD_VM_Local_Test


class SD_SVS_Disp_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-svs-disp"
        super(SD_SVS_Disp_Tests, self).setUp()

    def test_packages_installed(self):
        for package in ['securedrop-workstation-svs-disp', 'nautilus',
                        'totem', 'libreoffice']:
            self.assertTrue(self._package_is_installed(package))

def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_SVS_Disp_Tests)
    return suite
