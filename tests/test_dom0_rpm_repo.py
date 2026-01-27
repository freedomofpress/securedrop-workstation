import subprocess

import dnf  # Implicit dom0 dependency
import pytest

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


def _is_installed(pkg: str) -> bool:
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


def test_rpm_releasever_substitution():
    """
    Ensure DNF is understanding $releasever as we expect in the repository
    URL structure.
    """
    qubes_version = dnf.rpm.detect_releasever("/")
    assert qubes_version in ["4.2", "4.3"]


@pytest.fixture(scope="session")
def repo_config(dom0_config):
    """
    Look up the appropriate Yum repo configuration, based on config.json.
    Depends on the `dom0_config` fixture, for lookup on the environment,
    which determines the rpm config.
    """
    # The dom0 fixture defaults to "dev" for the environment key.
    # It's possible that we can fall back to inferring the env based on
    # which keyring RPM packages are installed in dom0.
    env = dom0_config["environment"]
    return REPO_CONFIG[env].copy()


def test_rpm_repo_config(repo_config):
    """
    Inspect the dom0 yum repo config for the SecureDrop Workstation RPM repository,
    and verify the settings are what we expect. Some of the attributes vary
    by env; see top-level REPO_CONFIG.
    """
    repo = repo_config["repo_file_name"]
    baseurl = repo_config["yum_repo_url"]
    repo_file = f"/etc/yum.repos.d/{repo}"
    wanted_lines = [
        "[securedrop-workstation-dom0]",
        "gpgcheck=1",
        "skip_if_unavailable=False",
        "gpgkey=file://{}".format(repo_config.get("signing_key")),
        "enabled=1",
        f"baseurl={baseurl}",
        "name=SecureDrop Workstation Qubes dom0 repo",
    ]
    with open(repo_file) as f:
        found_lines = [x.strip() for x in f.readlines()]

    assert found_lines == wanted_lines


def test_dom0_has_keyring_package(dom0_config):
    """
    Confirm that the "securedrop-workstation-keyring" package is installed in dom0,
    and that the variant of the package is appropriate for the configured env,
    e.g. dev vs prod.
    """
    env = dom0_config["environment"]
    # Prod keyring is always installed
    assert _is_installed("securedrop-workstation-keyring")

    # TODO: remove this check when config.json does not specify
    # "environment" anymore.
    # Until then, the order matters; a dev setup may also have
    # a staging package, but not vice-versa.
    if env == "dev":
        assert _is_installed("securedrop-workstation-keyring-dev")
    elif env == "staging":
        assert _is_installed("securedrop-workstation-keyring-staging")
