import os
import unittest


# TODO: add actual integration testing of policies
class SD_Qubes_Rpc_Tests(unittest.TestCase):
    def test_policies(self):
        """verify the policies are installed"""
        assert os.path.exists("/etc/qubes/policy.d/31-securedrop-workstation.policy")
        assert os.path.exists("/etc/qubes/policy.d/32-securedrop-workstation.policy")
