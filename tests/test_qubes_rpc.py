import os
import unittest


# TODO: add actual integration testing of policies
class SD_Qubes_Rpc_Tests(unittest.TestCase):
    def test_policies(self):
        """verify the policies are installed"""
        assert os.path.exists("/etc/qubes/policy.d/70-securedrop-workstation.policy")
        assert os.path.exists("/etc/qubes/policy.d/60-securedrop-workstation.policy")


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Qubes_Rpc_Tests)
    return suite
