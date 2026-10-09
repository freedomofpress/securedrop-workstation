import json
import subprocess
import sys
from pathlib import Path
from shlex import quote

from qubesadmin import Qubes

from securedrop_manage import (
    CONFIG_FILENAME,
    CONFIG_PATH,
    SUBMISSION_KEY_FILENAME,
    ManageException,
)
from securedrop_manage.products import Product
from securedrop_manage.validate import validate_config

TAILS_PATH = Path("/run/media/user/TailsData/")
TAILS_GNUPG_PATH = TAILS_PATH / "gnupg/"
TAILS_ADMIN_CONFIG_PATH = TAILS_PATH / "securedrop-admin/"
TAILS_PKG_JOURNALIST_INTERFACE_CONFIG = TAILS_ADMIN_CONFIG_PATH / "app-journalist.auth_private"
TAILS_GIT_JOURNALIST_INTERFACE_CONFIG = (
    TAILS_PATH / "Persistent/securedrop/install_files/ansible-base/app-journalist.auth_private"
)
TAILS_SSH_PATH = TAILS_PATH / "openssh-client/"

SD_ADMIN_VM = "sd-admin"
SD_ADMIN_CONFIG_PATH = "/home/user/.config/securedrop-admin"
SD_ADMIN_SSH_PATH = "/home/user/.ssh"
SD_ADMIN_STAGING_PATH = "/home/user/.securedrop-admin-import"
SET_SITE_SPECIFIC = "securedrop-set-site-specific"

DEFAULT_SD_APP_GB = 10
DEFAULT_SD_LOG_GB = 5


def extract_secret_key_fingerprints(gpg_output: str) -> list[str]:
    """
    Parses gpg output to return fingerprints for all secret keys in the keyring.
    """
    lines = gpg_output.strip().split("\n")
    fingerprints = []

    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        if idx >= len(lines) - 1:
            continue

        fields = line.split(":")
        record_type = fields[0]

        # Secret key
        if record_type == "sec":
            # Following line should be the secret key fingerprint
            fpr_fields = lines[idx + 1].split(":")
            if fpr_fields[0] == "fpr" and len(fpr_fields) > 9 and fpr_fields[9]:
                fingerprints.append(fpr_fields[9])

    return fingerprints


def _prompt_choose_submission_key(fingerprints: list[str]) -> str | None:
    print(
        "Multiple eligible secret keys found in the keyring.\n"
        "Please select which secret key to use as the SecureDrop submission key.\n\n"
    )
    for i, fpr_option in enumerate(fingerprints, 1):
        print(f"{i}. {fpr_option}")
    try:
        choice = int(input(f"Submission key [1-{len(fingerprints)}]: "))
        if 1 <= choice <= len(fingerprints):
            fingerprint = fingerprints[choice - 1]
            print(f"Selected key {choice}: {fingerprint}")
            return fingerprint
        else:
            print("Invalid choice. Exiting.")
            return None
    except ValueError:
        print("Invalid input. Exiting.")
        return None


def _try_read_submission_key() -> str | None:
    """
    Checks if SecureDrop submission key is written to dom0. If so, returns
    submission key fingerprint
    """
    key_file = CONFIG_PATH / SUBMISSION_KEY_FILENAME
    if not key_file.exists():
        return None
    gpg_output = subprocess.check_output(
        ["gpg", "--show-keys", "--with-fingerprint", "--with-colon", key_file],
        text=True,
    )
    fingerprints = extract_secret_key_fingerprints(gpg_output)
    if len(fingerprints) == 0:
        raise ManageException("Error reading submission key: no private keys found")
    if len(fingerprints) > 1:
        fingerprint = _prompt_choose_submission_key(fingerprints)
        if not fingerprint:
            raise ManageException(
                "Error reading submission key: unable to select from multiple eligible keys"
            )
        return fingerprint
    else:
        return fingerprints[0]


def import_submission_key() -> str:
    """
    Imports SecureDrop submission key from USB drive to dom0. Assumes that the USB drive
    is successfully attached to vault VM and decrypted.
    Returns the submission key fingerprint.
    """
    gpg_output = subprocess.check_output(
        [
            "qvm-run",
            "--pass-io",
            "vault",
            f"gpg --homedir {TAILS_GNUPG_PATH} -K --fingerprint --with-colon",
        ],
        text=True,
    )
    fingerprints = extract_secret_key_fingerprints(gpg_output)
    if len(fingerprints) == 0:
        raise ManageException("Error reading submission key fingerprint: no private keys found")
    if len(fingerprints) > 1:
        fingerprint = _prompt_choose_submission_key(fingerprints)
        if not fingerprint:
            raise ManageException(
                "Error importing submission key: unable to select from multiple eligible keys"
            )
    else:
        fingerprint = fingerprints[0]

    gpg_privkey = subprocess.check_output(
        [
            "qvm-run",
            "--pass-io",
            "vault",
            f"gpg --homedir {TAILS_GNUPG_PATH} --export-secret-keys --armor {fingerprint}",
        ],
        text=True,
    )

    temp_file = f"/tmp/{SUBMISSION_KEY_FILENAME}"
    with open(temp_file, "w") as f:
        f.write(gpg_privkey)

    subprocess.check_call(["cp", temp_file, CONFIG_PATH])

    return fingerprint


def import_journalist_interface_config() -> tuple[str, str]:
    """
    Imports Journalist Interface address and authentication info from USB drive to dom0.
    Assumes that USB drive is attached to vault VM and decrypted.
    Returns (hostname, key) of the journalist interface hidserv
    """
    journalist_interface_config = ""
    try:
        # First, check for the 2.13.0+ location
        journalist_interface_config = subprocess.check_output(
            [
                "qvm-run",
                "--pass-io",
                "vault",
                f"cat {TAILS_PKG_JOURNALIST_INTERFACE_CONFIG}",
            ],
            text=True,
        )
    except subprocess.CalledProcessError:
        try:
            # Fall back to the legacy location
            journalist_interface_config = subprocess.check_output(
                [
                    "qvm-run",
                    "--pass-io",
                    "vault",
                    f"cat {TAILS_GIT_JOURNALIST_INTERFACE_CONFIG}",
                ],
                text=True,
            )
        except subprocess.CalledProcessError:
            raise ManageException(
                "Failed to find a valid journalist interface config.\n"
                "Check the attached USB key and try again."
            )

    fields = journalist_interface_config.strip().split(":")
    addr = fields[0]
    auth_token = fields[3]
    return addr, auth_token


def import_journalist_config() -> None:
    submission_key_fingerprint = _try_read_submission_key()
    if not submission_key_fingerprint:
        subprocess.Popen(
            [
                "qvm-start",
                "vault",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(
            "Preparing to import SecureDrop submission key from USB...\n\n\n"
            "Ensure that USB containing submission key is connected.\n\n"
            "1. Attach the USB to the vault VM\n"
            "2. Open File Manager in the vault VM\n"
            "3. Select the USB drive in the left sidebar of the file manager.\n"
            "It should be listed under Devices as 'N GB Encrypted'.\n"
            "Enter the correct passphrase when prompted.\n\n"
            "Note: you may see an error 'Failed to open directory TailsData'.\n"
            "This can safely be ignored and the import can still proceed.\n\n"
        )
        response = input("Are you ready to proceed (y/N)? ")
        if response.lower() != "y":
            print("Exiting.")
            return
        print("Importing submission key...")
        submission_key_fingerprint = import_submission_key()
        print(
            "Submission key import complete!\n"
            "Please detach and disconnect the USB containing the submission key\n\n"
        )
    else:
        print("Found submission key file, proceeding")

    try:
        validate_config(CONFIG_PATH, Product.JOURNALIST)
        print("Valid configuration found, configuration complete")
    except ManageException:
        subprocess.Popen(
            ["qvm-start", "vault", "--skip-if-running"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(
            "Importing Journalist Interface details...\n\n\n"
            "Ensure that Admin Workstation or Journalist Workstation USB is connected.\n\n"
            "1. Attach the USB to the vault VM\n"
            "2. Open Thunar File Manager in the vault VM\n"
            "3. Select the USB drive in the left sidebar of the file manager.\n"
            "It should be listed under Devices as 'N GB Encrypted'.\n"
            "Enter the correct passphrase when prompted.\n\n"
        )
        response = input("Are you ready to proceed (y/N)? ")
        if response.lower() != "y":
            print("Exiting.")
            return
        try:
            ji_addr, ji_auth_token = import_journalist_interface_config()
        except ManageException as e:
            print(f"Error importing configuration: {e}")
            sys.exit(1)

        print(
            "Journalist Interface details imported.\n\n"
            f"Onion address: {ji_addr}.onion\n"
            f"Auth token: {ji_auth_token}\n"
        )
        response = input("Confirm that these values are correct to proceed (y/N) ")
        if response.lower() != "y":
            print("Exiting.")
            return

        config = {
            "submission_key_fpr": submission_key_fingerprint,
            "hidserv": {
                "hostname": ji_addr + ".onion",
                "key": ji_auth_token,
            },
            "environment": "prod",
            "vmsizes": {"sd_app": DEFAULT_SD_APP_GB, "sd_log": DEFAULT_SD_LOG_GB},
        }
        temp_file = f"/tmp/{CONFIG_FILENAME}"
        with open(temp_file, "w") as f:
            json.dump(config, f, indent=2)
        subprocess.check_call(["cp", temp_file, CONFIG_PATH])
        print(
            "Journalist Interface import complete!\nPlease detach and disconnect the USB drive.\n\n"
        )
        print("Validating configuration...")
        validate_config(CONFIG_PATH, Product.JOURNALIST)
        print("Validation successful!")


def _check_in_qube(vm: str, command: str) -> bool:
    """
    Runs a shell command in the given qube, returning whether it exited successfully
    """
    result = subprocess.run(
        ["qvm-run", "--pass-io", vm, command],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _pipe_admin_file(source: str, destination: str) -> None:
    """
    Streams a file from vault to sd-admin
    """
    reader = subprocess.Popen(
        ["qvm-run", "--pass-io", "vault", f"cat {quote(source)}"], stdout=subprocess.PIPE
    )
    try:
        writer = subprocess.run(
            ["qvm-run", "--pass-io", SD_ADMIN_VM, f"umask 077 && cat > {quote(destination)}"],
            stdin=reader.stdout,
            check=False,
        )
    finally:
        # Let vault see a closed pipe if sd-admin stops reading early
        if reader.stdout:
            reader.stdout.close()
        reader_returncode = reader.wait()

    if reader_returncode != 0 or writer.returncode != 0:
        raise ManageException(f"Error copying {source} from vault to {SD_ADMIN_VM}")


def copy_admin_config() -> list[str]:
    """
    Copies the securedrop-admin configuration and SSH keys from the Tails USB in vault to
    sd-admin. Returns the names of the files now in sd-admin's config directory.
    """
    config = quote(SD_ADMIN_CONFIG_PATH)
    ssh = quote(SD_ADMIN_SSH_PATH)
    # Stage everything first so that a failed transfer doesn't touch the existing config
    staging = quote(SD_ADMIN_STAGING_PATH)
    staging_config = quote(f"{SD_ADMIN_STAGING_PATH}/config")
    cleanup = f"rm -rf {staging}"

    try:
        names = subprocess.check_output(
            [
                "qvm-run",
                "--pass-io",
                "vault",
                f"find {quote(str(TAILS_ADMIN_CONFIG_PATH))} -maxdepth 1 -type f -printf '%f\\n'",
            ],
            text=True,
        ).splitlines()
    except subprocess.CalledProcessError:
        raise ManageException("Error listing securedrop-admin configuration in vault")

    try:
        if not _check_in_qube(
            SD_ADMIN_VM, f"{cleanup} && mkdir -m 700 {staging} && mkdir -m 700 {staging_config}"
        ):
            raise ManageException(f"Error preparing {SD_ADMIN_STAGING_PATH} in {SD_ADMIN_VM}")
        for name in names:
            _pipe_admin_file(
                str(TAILS_ADMIN_CONFIG_PATH / name), f"{SD_ADMIN_STAGING_PATH}/config/{name}"
            )
        _pipe_admin_file(str(TAILS_SSH_PATH / "id_rsa"), f"{SD_ADMIN_STAGING_PATH}/id_rsa")
        _pipe_admin_file(str(TAILS_SSH_PATH / "id_rsa.pub"), f"{SD_ADMIN_STAGING_PATH}/id_rsa.pub")

        install: list[str] = []
        if _check_in_qube(SD_ADMIN_VM, f"command -v {SET_SITE_SPECIFIC}"):
            install.append(
                f"{SET_SITE_SPECIFIC} --file {staging_config}/site-specific config_path {config}"
            )
        else:
            print(
                f"{SET_SITE_SPECIFIC} not found in {SD_ADMIN_VM}; "
                "not updating config_path in site-specific."
            )
        install += [
            f"mkdir -p -m 700 {ssh}",
            f"install -m 600 {staging}/id_rsa {ssh}/id_rsa",
            f"install -m 644 {staging}/id_rsa.pub {ssh}/id_rsa.pub",
            f"rm -rf {config}",
            f"mv {staging_config} {config}",
            f"ls -1A {config}",
        ]
        try:
            files = subprocess.check_output(
                ["qvm-run", "--pass-io", SD_ADMIN_VM, " && ".join(install)], text=True
            )
        except subprocess.CalledProcessError as e:
            raise ManageException(
                f"Error installing securedrop-admin configuration in {SD_ADMIN_VM}: {e}"
            )
    finally:
        _check_in_qube(SD_ADMIN_VM, cleanup)
    return files.split()


def import_admin_config() -> None:
    """
    Imports the securedrop-admin configuration from an Admin Workstation Tails USB into
    sd-admin. Assumes the USB will be attached to vault and its persistent storage unlocked.
    """
    if SD_ADMIN_VM not in Qubes().domains:
        raise ManageException(
            f"{SD_ADMIN_VM} does not exist. Provision the Admin Workstation before configuring it."
        )

    existing = [
        path
        for path in (SD_ADMIN_CONFIG_PATH, f"{SD_ADMIN_SSH_PATH}/id_rsa")
        if _check_in_qube(SD_ADMIN_VM, f"stat {quote(path)} > /dev/null")
    ]
    if existing:
        print(f"{SD_ADMIN_VM} already has securedrop-admin configuration in {', '.join(existing)}")
        response = input("Replace it with the configuration from the USB (y/N)? ")
        if response.lower() != "y":
            print("Exiting.")
            return

    subprocess.Popen(
        ["qvm-start", "vault", "--skip-if-running"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(
        "Preparing to import Admin Workstation configuration from USB...\n\n\n"
        "Ensure that the Admin Workstation USB is connected.\n\n"
        "1. Attach the USB to the vault VM\n"
        "2. Open File Manager in the vault VM\n"
        "3. Select the USB drive in the left sidebar of the file manager.\n"
        "It should be listed under Devices as 'N GB Encrypted'.\n"
        "Enter the correct passphrase when prompted.\n\n"
        "Note: you may see an error 'Failed to open directory TailsData'.\n"
        "This can safely be ignored and the import can still proceed.\n\n"
    )
    response = input("Are you ready to proceed (y/N)? ")
    if response.lower() != "y":
        print("Exiting.")
        return

    print("Importing Admin Workstation configuration...")
    tails_config = quote(str(TAILS_ADMIN_CONFIG_PATH))
    # TODO(vicki): automatically handle the migration from git-based installer
    if not _check_in_qube("vault", f"test -d {tails_config}"):
        raise ManageException(
            f"No securedrop-admin configuration found at {TAILS_ADMIN_CONFIG_PATH} in vault.\n"
            "Check that the USB is attached to vault and unlocked. If this Admin Workstation\n"
            "still uses the git-based installer, migrate it to the securedrop-admin package\n"
            "in Tails first."
        )
    if not _check_in_qube("vault", f"test -f {tails_config}/site-specific"):
        raise ManageException(
            f"No site-specific file found in {TAILS_ADMIN_CONFIG_PATH}.\n"
            "This looks like a Journalist Workstation USB; attach an Admin Workstation USB instead."
        )
    ssh_keys = f"{TAILS_SSH_PATH}/id_rsa {TAILS_SSH_PATH}/id_rsa.pub"
    if not _check_in_qube("vault", f"stat {ssh_keys} > /dev/null"):
        raise ManageException(
            f"No SSH keys found in {TAILS_SSH_PATH}.\n"
            "Check that SSH Client persistence is enabled on the Admin Workstation USB."
        )

    print(f"Copying configuration to {SD_ADMIN_VM}...")
    files = copy_admin_config()
    print(
        f"Admin Workstation configuration imported into {SD_ADMIN_VM}:\n"
        + "".join(f"  - {name}\n" for name in files)
        + f"SSH keys imported into {SD_ADMIN_SSH_PATH}.\n"
        + "\nPlease detach and disconnect the USB drive.\n\n"
        f"Next, open a terminal in {SD_ADMIN_VM} and run:\n\n"
        "  securedrop-admin qubesconfig\n\n"
        "to set up Tor access and SSH aliases for the SecureDrop servers."
    )
