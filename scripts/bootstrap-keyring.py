#!/usr/bin/env python3
import argparse
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TEST_KEY_FILENAME = "test_key.asc"
YUM_REPOS_DIR = "/etc/yum.repos.d"
KEYRING_PACKAGENAME = "securedrop-workstation-keyring"

# Test key: ID is deterministic and based on fpr + key creation timestamp
TEST_KEY_RPMID = "gpg-pubkey-3fab65ab-660f2beb"

# Only support test rpms; for prod, use official install instructions
BASEURL = "https://yum-test.securedrop.org"


def get_fedora_version():
    return subprocess.check_output(["rpm", "--eval", "%{fedora}"]).decode().strip()


def create_repo_file(env: str, repo_file_path: str, ver: str):
    """Create .repo file based on environment."""
    repo_content = f"""
[{KEYRING_PACKAGENAME}-{env}]
enabled=0
gpgcheck=1
baseurl={BASEURL}/workstation/dom0/f{ver}{'-nightlies' if env == 'dev' else ''}
name=SecureDrop Workstation Keyring ({env})
"""
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


def dom0_install_keyring(env: str | None = None):
    """Use qubes-dom0-update to install keyring package."""
    args = ["sudo", "qubes-dom0-update", "-y"]

    if env:
        package_name = f"{KEYRING_PACKAGENAME}-{env}"
        args.append(f"--enablerepo={package_name}")
    else:
        package_name = KEYRING_PACKAGENAME
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

    fedora_version = get_fedora_version()

    # Build .repo file, then install with correct permissions in /etc/yum.repos.d (owned by root)
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_file_path = Path(temp_dir) / f"{KEYRING_PACKAGENAME}-{args.env}.repo"

        create_repo_file(args.env, repo_file_path, fedora_version)
        repo_dest_path = Path(YUM_REPOS_DIR) / f"{KEYRING_PACKAGENAME}-{args.env}.repo"
        subprocess.check_call(
            ["sudo", "install", "-m", "0644", str(repo_file_path), str(repo_dest_path)]
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

    # Install prod keyring hosted in yum-test to satisfy dom0 config dependency.
    # When the prod keyring reaches Qubes-Contrib, this can be removed.
    dom0_install_keyring()


if __name__ == "__main__":
    main()
