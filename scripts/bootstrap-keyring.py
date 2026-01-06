#!/usr/bin/env python3
"""
This is a developer script to handle establishing signing key prerequisites for dom0,
so that developer machines running a "dev" environment of the SecureDrop Workstation
can install packages from remote sources, both prod and testing.

This script configures a yum repo in dom0 and pulls in the necessary keyring packages
to unblock use of the standard "sdw-admin" install flow. The script is necessary to encapsulate
full config coverage within the "make dev" target; otherwise, developers would need
to set up qubes-contrib and install packages manually, for prod packages, and then
do the same for yum-test repos, which is an unpleasant and tedious workflow.
"""

import argparse
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TEST_KEY_FILENAME = "test_key.asc"
YUM_REPOS_DIR = "/etc/yum.repos.d"
KEYRING_PACKAGENAME = "securedrop-workstation-keyring"
YUM_REPO_BASENAME = "securedrop-workstation-dom0"

# Test key: ID is deterministic and based on fpr + key creation timestamp
TEST_KEY_RPMID = "gpg-pubkey-3fab65ab-660f2beb"

# Only support test rpms; for prod, use official install instructions
BASEURL = "https://yum-test.securedrop.org"


def create_repo_file(env: str, repo_file_path: str):
    """Create .repo file based on environment."""
    repo_content = f"""
[{YUM_REPO_BASENAME}-{env}]
gpgcheck=1
skip_if_unavailable=False
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test
enabled=0
baseurl=https://yum-test.securedrop.org/workstation/dom0/r$releasever{'-nightlies' if env == 'dev' else ''}
name=SecureDrop Workstation Qubes dom0 repo ({env})
"""  # noqa: E501
    with open(repo_file_path, "w") as repo_file:
        repo_file.write(repo_content.lstrip())


def rpm_import(key_file: Path):
    """Import GPG key into rpmdb."""
    subprocess.check_call(["sudo", "rpm", "--import", str(key_file)])


def is_key_imported(rpm_id: str):
    """Check rpmdb for key with givem rpm_id."""
    try:
        subprocess.check_call(["rpm", "-q", rpm_id])
        return True
    except subprocess.CalledProcessError:
        return False


def dom0_install_keyring(env: str):
    """Use qubes-dom0-update to install keyring package."""
    args = ["sudo", "qubes-dom0-update", "--clean", "-y"]

    package_name = f"{KEYRING_PACKAGENAME}-{env}"
    args.append(f"--enablerepo={YUM_REPO_BASENAME}-{env}")
    args.append(package_name)
    subprocess.check_call(args)


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap SecureDrop Workstation keyring on QubesOS"
    )
    parser.add_argument(
        "--env",
        choices=["dev", "staging"],
        required=True,
        help="Specify the environment ('dev' or 'staging')",
    )

    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    key_file = script_dir / TEST_KEY_FILENAME
    if not key_file.exists():
        print(f"'{key_file}' not found.")
        sys.exit(1)

    # Build .repo file, then install with correct permissions in /etc/yum.repos.d (owned by root)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_src_path = Path(temp_dir) / f"{YUM_REPO_BASENAME}-{args.env}.repo"

        create_repo_file(args.env, repo_src_path)
        repo_dest_path = Path(YUM_REPOS_DIR) / f"{YUM_REPO_BASENAME}-{args.env}.repo"
        subprocess.check_call(
            ["sudo", "install", "-m", "0644", str(repo_src_path), str(repo_dest_path)]
        )

    # Install environment-specific keyring package
    rpm_import(key_file)

    if not is_key_imported(TEST_KEY_RPMID):
        print("Wait for key import ...")
        time.sleep(20)

    if not is_key_imported(TEST_KEY_RPMID):
        print(f"Key {TEST_KEY_RPMID} ({TEST_KEY_FILENAME}) not found in rpm db.")
        sys.exit(1)

    dom0_install_keyring(args.env)


if __name__ == "__main__":
    main()
