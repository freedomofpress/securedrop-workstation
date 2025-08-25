import json
from pathlib import Path
from string import Template

import pytest

PROJ_ROOT = Path(__file__).parent.parent
FEDORA_VERSION = "f37"

REPO_CONFIG = {
    "prod": {
        "signing_key": "/etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation",
        "signing_key_fpr": "2359E6538C0613E652955E6C188EDD3B7B22E6A3",
        "signing_key_uid": "SecureDrop Release Signing Key <securedrop-release-key-2021@freedom.press>",  # noqa: E501
        "signing_key_exp": "2027",
        "repo_file_name": "securedrop-workstation-dom0.repo",
        "yum_repo_url": "https://yum.securedrop.org/workstation/dom0/$FEDORA_VERSION/",
    },
    "dev": {
        "signing_key": "/etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test",
        "signing_key_fpr": "83127F68BABB04F3FE9A69AA545E94503FAB65AB",
        "signing_key_uid": "SecureDrop TESTING key <securedrop@freedom.press>",
        "signing_key_exp": "-1",
        "repo_file_name": "securedrop-workstation-dom0-dev.repo",
        "yum_repo_url": "https://yum-test.securedrop.org/workstation/dom0/$FEDORA_VERSION-nightlies/",
    },
    "staging": {
        "signing_key": "/etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test",
        "signing_key_fpr": "83127F68BABB04F3FE9A69AA545E94503FAB65AB",
        "signing_key_uid": "SecureDrop TESTING key <securedrop@freedom.press>",
        "signing_key_exp": "-1",
        "repo_file_name": "securedrop-workstation-dom0-staging.repo",
        "yum_repo_url": "https://yum-test.securedrop.org/workstation/dom0/$FEDORA_VERSION/",
    },
}


@pytest.fixture
def dom0_config():
    """Make the dom0 "config.json" available to tests."""
    with open(PROJ_ROOT / "config.json") as config_file:
        return json.load(config_file)


@pytest.fixture
def env():
    """
    Check build variant based on installed .repo filename.
    Developers who are experimenting with additional disabled .repo files in
    /etc/yum.repos.d/ should ensure no naming collisions with securedrop-workstation-keyring
    files, per REPO_CONFIG above or per the securedrop-workstation-keyring rpm spec file.
    """
    # Order matters due to package versioning
    for env_type in ["dev", "staging", "prod"]:
        repo_filename = REPO_CONFIG[env_type]["repo_file_name"]
        repo_path = Path(f"/etc/yum.repos.d/{repo_filename}")
        if repo_path.exists:
            return env_type

    pytest.fail("Misconfigured environment, env could not be determined.")


@pytest.fixture
def config(env):
    config = REPO_CONFIG[env].copy()

    # Fedora version is a placeholder, so fix that
    config["yum_repo_url"] = Template(config["yum_repo_url"]).safe_substitute(
        {"FEDORA_VERSION": FEDORA_VERSION}
    )
    return config
