import io
import os
import unittest

import yaml


class SD_Qubes_Rpc_Tests(unittest.TestCase):
    def setUp(self):
        self.expected = self._loadVars()

    def tearDown(self):
        pass

    def test_Policies(self):
        # Using a for loop instead of pytest.parametrize due to
        # the absence of pytest in dom0.
        fail = False
        for policy in self.expected:
            if not self._startsWith(policy["policy"], policy["starts_with"]):
                fail = True
        self.assertFalse(fail), "Policy does not match: " + policy["policy"]

    def _startsWith(self, filename, expectedPolicy):
        filePath = filename
        # The Qubes 4.0 grants assumed all policies were in the same dir.
        # Support that for backwards-compatibility on 4.0, but we'll use
        # absolute paths in the test vars from 4.1 onward.
        if not filePath.startswith("/"):
            filePath = os.path.join("/etc/qubes-rpc/policy", filename)

        with io.open(filePath, "r") as f:
            actualPolicy = f.read()
            if actualPolicy.startswith(expectedPolicy):
                return True
            else:
                print("\n\n#### BEGIN RPC policy error report ####\n\n")
                print("Policy for {} is:\n{}".format(filename, actualPolicy))
                print("Policy for {} should be:\n{}".format(filename, expectedPolicy))
                print("\n\n#### END RPC policy error report ####\n\n")
                return False

    def _loadVars(self):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vars", "qubes-rpc.yml")
        with io.open(filepath, "r") as f:
            data = yaml.safe_load(f)
        return data


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Qubes_Rpc_Tests)
    return suite
