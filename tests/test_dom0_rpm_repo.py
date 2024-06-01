import json
import unittest

DEBIAN_VERSION = "bookworm"
FEDORA_VERSION = "f37"


class SD_Dom0_Rpm_Repo_Tests(unittest.TestCase):
    pubkey_wanted = ""
    yum_repo_url = ""
    pubkey_actual = "/etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation"
    pubkey_wanted_prod = "securedrop_salt/securedrop-release-signing-pubkey-2021.asc"
    pubkey_wanted_test = "securedrop_salt/apt-test-pubkey.asc"
    yum_repo_url_prod = f"https://yum.securedrop.org/workstation/dom0/{FEDORA_VERSION}"
    yum_repo_url_test = f"https://yum-test.securedrop.org/workstation/dom0/{FEDORA_VERSION}"

    def setUp(self):
        # Enable full diff output in test report, to aid in debugging
        self.maxDiff = None
        with open("config.json") as c:
            config = json.load(c)
            if "environment" not in config:
                config["environment"] = "dev"

            if config["environment"] == "prod":
                self.pubkey_wanted = self.pubkey_wanted_prod
                self.yum_repo_url = self.yum_repo_url_prod
            else:
                self.pubkey_wanted = self.pubkey_wanted_test
                self.yum_repo_url = self.yum_repo_url_test

    def test_rpm_repo_public_key(self):
        with open(self.pubkey_actual) as f:
            pubkey_actual_contents = f.readlines()

        with open(self.pubkey_wanted) as f:
            pubkey_wanted_contents = f.readlines()

        self.assertEqual(pubkey_actual_contents, pubkey_wanted_contents)

    def test_rpm_repo_config(self):
        repo_file = "/etc/yum.repos.d/securedrop-workstation-dom0.repo"
        wanted_lines = [
            "[securedrop-workstation-dom0]",
            "gpgcheck=1",
            "skip_if_unavailable=False",
            "gpgkey=file://{}".format(self.pubkey_actual),  # noqa
            "enabled=1",
            f"baseurl={self.yum_repo_url}",
            "name=SecureDrop Workstation Qubes dom0 repo",
        ]
        with open(repo_file) as f:
            found_lines = [x.strip() for x in f.readlines()]

        self.assertEqual(found_lines, wanted_lines)


def load_tests(loader, tests, pattern):
    return unittest.TestLoader().loadTestsFromTestCase(SD_Dom0_Rpm_Repo_Tests)
