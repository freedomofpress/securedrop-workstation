import json
import subprocess
import unittest

import dnf  # Implicit dom0 dependency

REPO_CONFIG = {
    "prod": {
        "signing_key": "/etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation",
        "repo_file_name": "securedrop-workstation-dom0.repo",
        "yum_repo_url": "https://yum.securedrop.org/workstation/dom0/r$releasever",
    },
    "dev": {
        "signing_key": "/etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test",
        "repo_file_name": "securedrop-workstation-dom0-dev.repo",
        "yum_repo_url": "https://yum-test.securedrop.org/workstation/dom0/r$releasever-nightlies",
    },
    "staging": {
        "signing_key": "/etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test",
        "repo_file_name": "securedrop-workstation-dom0-staging.repo",
        "yum_repo_url": "https://yum-test.securedrop.org/workstation/dom0/r$releasever",
    },
}


class SD_Dom0_Rpm_Repo_Tests(unittest.TestCase):
    def setUp(self):
        # Enable full diff output in test report, to aid in debugging
        self.maxDiff = None

        with open("config.json") as c:
            config = json.load(c)
            self.env = config.get("environment")

            # Fall back to checking environment via keyring package
            # (will eventually replace config.json environment)
            if not self.env:
                self.env = self._get_env_by_package()

        self.config = REPO_CONFIG[self.env]

    def test_rpm_repo_config(self):
        repo = self.config["repo_file_name"]
        baseurl = self.config["yum_repo_url"]
        repo_file = f"/etc/yum.repos.d/{repo}"
        wanted_lines = [
            "[securedrop-workstation-dom0]",
            "gpgcheck=1",
            "skip_if_unavailable=False",
            "gpgkey=file://{}".format(self.config.get("signing_key")),
            "enabled=1",
            f"baseurl={baseurl}",
            "name=SecureDrop Workstation Qubes dom0 repo",
        ]
        with open(repo_file) as f:
            found_lines = [x.strip() for x in f.readlines()]

        assert found_lines == wanted_lines

    def test_rpm_releasever_substitution(self):
        """
        Ensure DNF is understanding $releasever as we expect in the repository
        URL structure.
        """
        qubes_version = dnf.rpm.detect_releasever("/")
        assert qubes_version in ["4.2", "4.3"]

    def _get_env_by_package(self):
        """
        Check which environment we are using by checking keyring package.
        The order matters; due to package versioning, an installed dev package
        means a dev setup, so check dev, staging, then prod.
        """
        for env, suffix in [("dev", "-dev"), ("staging", "-staging"), ("prod", "")]:
            if self._is_installed(f"securedrop-workstation-keyring{suffix}"):
                return env
        self.fail("No keyring package")
        # Unreachable, but ruff was unhappy
        return None

    def _is_installed(self, pkg: str):
        """
        Check if package is installed.
        """
        try:
            subprocess.check_call(
                ["rpm", "-q", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            return True
        except subprocess.CalledProcessError:
            return False

    def test_dom0_has_keyring_package(self):
        # Prod keyring is always installed
        assert self._is_installed("securedrop-workstation-keyring")

        # TODO: remove this check when config.json does not specify
        # "environment" anymore.
        # Until then, the order matters; a dev setup may also have
        # a staging package, but not vice-versa.
        if self.env == "dev":
            assert self._is_installed("securedrop-workstation-keyring-dev")
        elif self.env == "staging":
            assert self._is_installed("securedrop-workstation-keyring-staging")
