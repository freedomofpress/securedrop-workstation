#!/usr/bin/env python3
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

TEST_KEY_FILENAME = "test_key.asc"
YUM_REPOS_DIR = "/etc/yum.repos.d"
KEYRING_PACKAGENAME = "securedrop-workstation-keyring"

# Only support test rpms; for prod, use official install instructions
BASEURL = "https://yum-test.securedrop.org"


def get_fedora_version():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("VERSION_ID="):
                    version = line.split("=")[1].strip().strip('"')
                    if version == "4.2":
                        return "37"
                    elif version == "4.3":
                        return "41"
    except Exception as e:
        print(f"Error retrieving Fedora version: {e}")
        sys.exit(1)

    print("No Fedora version number found.")
    sys.exit(1)


def create_repo_file(env, repo_file_path, ver):
    """Creates the .repo file based on environment."""
    repo_content = f"""
[{KEYRING_PACKAGENAME}-{env}]
enabled=1
gpgcheck=1
baseurl={BASEURL}/workstation/dom0/f{ver}{'-nightlies' if env == 'dev' else ''}
name=SecureDrop Workstation Keyring ({env})
"""
    with open(repo_file_path, "w") as repo_file:
        repo_file.write(repo_content.strip())


def rpm_import(key_file):
    """Imports the GPG key into the rpmdb."""
    subprocess.check_call(["sudo", "rpm", "--import", str(key_file)])


def dom0_install_keyring(env):
    """Use qubes-dom0-update to install correct keyring package."""
    package_name = f"{KEYRING_PACKAGENAME}-{env}"
    subprocess.check_call(["sudo", "qubes-dom0-update", "-y", package_name])


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

    # Build and install .repo file
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_file_path = Path(temp_dir) / f"{KEYRING_PACKAGENAME}-{args.env}.repo"

        create_repo_file(args.env, repo_file_path, fedora_version)
        repo_dest_path = Path(YUM_REPOS_DIR) / f"{KEYRING_PACKAGENAME}-{args.env}.repo"
        subprocess.check_call(
            ["sudo", "install", "-m", "0644", str(repo_file_path), str(repo_dest_path)]
        )

    # Install keyring package
    rpm_import(key_file)
    dom0_install_keyring(args.env)


if __name__ == "__main__":
    main()
