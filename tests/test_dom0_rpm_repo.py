import unittest


class SD_Dom0_Rpm_Repo_Tests(unittest.TestCase):

    def setUp(self):
        # Enable full diff output in test report, to aid in debugging
        self.maxDiff = None

    def test_rpm_repo_public_key(self):
        pubkey_actual = "/etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation"  # noqa
        pubkey_wanted = "sd-workstation/apt-test-pubkey.asc"

        with open(pubkey_actual, "r") as f:
            pubkey_actual_contents = f.readlines()

        with open(pubkey_wanted, "r") as f:
            pubkey_wanted_contents = f.readlines()

        self.assertEqual(pubkey_actual_contents, pubkey_wanted_contents)

    def test_rpm_repo_config(self):
        repo_file = "/etc/yum.repos.d/securedrop-workstation-dom0.repo"
        wanted_lines = [
            "[securedrop-workstation-dom0]",
            "gpgcheck=1",
            "gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation",  # noqa
            "enabled=1",
            "baseurl=https://yum-test.securedrop.org/workstation/dom0/f25",
            "name=SecureDrop Workstation Qubes dom0 repo",
        ]
        with open(repo_file, "r") as f:
            found_lines = [x.strip() for x in f.readlines()]

        self.assertEqual(found_lines, wanted_lines)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Dom0_Rpm_Repo_Tests)
    return suite
