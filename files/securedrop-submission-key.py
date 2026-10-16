#!/usr/bin/python3
"""
Generate a new Submission Key in dom0 and export the fingerprint, secret and public keys
"""

import argparse
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

import qubesadmin
from qubesadmin.exc import QubesException
from qubesadmin.vm import QubesVM

from securedrop_manage.configure import get_submission_key_fingerprint
from securedrop_manage.products import get_installed_product

# XDG_CONFIG_HOME is not set in 4.3 Qubes - set it manually
DOM0_CONFIG_DIR = Path.home() / ".config/securedrop-manage"
DOM0_SEC_KEY_PATH = DOM0_CONFIG_DIR / "sd-journalist.sec"
DOM0_PUB_KEY_PATH = DOM0_CONFIG_DIR / "sd-journalist.pub"
DOM0_CONFIG_PATH = DOM0_CONFIG_DIR / "config.json"

# Configurations in 'sd-admin' qube or for exporting via USB
SD_ADMIN_VM = "sd-admin"
SD_ADMIN_CONFIG_PATH = "~/.config/securedrop-admin"
SD_ADMIN_PUB_KEY_FILE_NAME = "SecureDrop.asc"
SD_ADMIN_PUB_KEY_PATH = f"{SD_ADMIN_CONFIG_PATH}/{SD_ADMIN_PUB_KEY_FILE_NAME}"
SD_ADMIN_SITE_SPECIFIC_PATH = f"{SD_ADMIN_CONFIG_PATH}/site-specific"

# ANSI color codes
BOLD = "\033[1m"
CYAN = "\033[36m"
RED = "\033[31m"
ITALIC = "\033[3m"
RESET = "\033[0m"


class SubmissionKeyException(Exception):
    pass


def generate_key(organization: str) -> tuple[str, str, str]:
    """
    Generate an RSA 4096 keypair with no expiry and no passphrase.
    """
    real_name = "SecureDrop"
    comment = f"[{organization}] SecureDrop Submission Key"
    params = "\n".join(
        [
            "%no-protection",
            "Key-Type: RSA",
            "Key-Length: 4096",
            "Key-Usage: sign",
            "Subkey-Type: RSA",
            "Subkey-Length: 4096",
            "Subkey-Usage: encrypt",
            f"Name-Real: {real_name}",
            f"Name-Comment: {comment}",
            "Expire-Date: 0",
            "%commit",
            "",
        ]
    )

    with tempfile.TemporaryDirectory(prefix="sd-submission-key-") as homedir:
        gpg = ["gpg", "--homedir", homedir, "--batch", "--no-tty", "--quiet"]
        subprocess.run(
            [*gpg, "--generate-key"],
            input=params,
            text=True,
            check=True,
        )
        listing = subprocess.check_output(
            [*gpg, "--list-secret-keys", "--with-colons", "--with-fingerprint"],
            text=True,
        )
        # The first "fpr" record after the "sec" record is the primary key
        fingerprints = []
        lines = listing.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("sec:"):
                fpr_line = lines[i + 1]
                if not fpr_line.startswith("fpr:"):
                    raise RuntimeError("Unable to determine fingerprint of generated key")
                fingerprints.append(fpr_line.split(":")[9])
        if len(fingerprints) != 1:
            raise RuntimeError(f"Expected exactly one generated key, found {len(fingerprints)}")
        fingerprint = fingerprints[0]

        armored_secret_key = subprocess.check_output(
            [*gpg, "--armor", "--export-secret-keys", fingerprint], text=True
        )
        armored_public_key = subprocess.check_output(
            [*gpg, "--armor", "--export", fingerprint], text=True
        )

    if not armored_secret_key.startswith("-----BEGIN PGP PRIVATE KEY BLOCK-----"):
        raise RuntimeError("Exported secret key is not an armored private key block")
    if not armored_public_key.startswith("-----BEGIN PGP PUBLIC KEY BLOCK-----"):
        raise RuntimeError("Exported public key is not an armored public key block")
    return fingerprint, armored_secret_key, armored_public_key


def write_private(path: Path, contents: str) -> None:
    """Write contents to path, ensuring it is only readable by the owner"""
    path.touch(mode=0o600)
    # touch() doesn't change the mode of an existing file
    path.chmod(0o600)
    path.write_text(contents)


def generate_submission_key(args: argparse.Namespace) -> None:
    if DOM0_SEC_KEY_PATH.exists() and not args.overwrite:
        print(
            f"Error: a submission key already exists at {DOM0_SEC_KEY_PATH}. "
            "Use --overwrite to overwrite it.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Generating submission key...")
    fingerprint, secret_key, public_key = generate_key(args.organization)

    DOM0_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    write_private(DOM0_SEC_KEY_PATH, secret_key)
    DOM0_PUB_KEY_PATH.write_text(public_key)

    # Edit or create config.json and set submission_key_fpr
    config = json.loads(DOM0_CONFIG_PATH.read_text()) if DOM0_CONFIG_PATH.exists() else {}
    config["submission_key_fpr"] = fingerprint
    DOM0_CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")

    print(f"Generated Submission Key with fingerprint: {fingerprint}")
    print(f"Secret key is saved to: {DOM0_SEC_KEY_PATH}")
    print(f"Public key is saved to: {DOM0_PUB_KEY_PATH}")


def copy_file_to_qube(
    local_path: str | Path,
    target_qube: QubesVM,
    target_path: str | Path,
    overwrite: bool,
    sudo: bool = False,
) -> None:
    # Check if file overriding allowed
    if not overwrite:
        try:
            target_qube.run(f"test ! -e {target_path}")
        except subprocess.CalledProcessError as e:
            raise SubmissionKeyException(
                f"a submission key already exists in '{target_qube.name}' at "
                f"{target_path}. Use --overwrite to overwrite it.",
            ) from e

    try:
        kwargs = {"user": "root"} if sudo else {}

        # Create path if it doesn't already exist
        target_qube.run(f"mkdir -p {Path(target_path).parent}", **kwargs)

        # Write file with default permissions
        with open(local_path, "rb") as pub_key_f:
            target_qube.run(f"tee {target_path}", input=pub_key_f.read(), **kwargs)
    except subprocess.CalledProcessError:
        raise SubmissionKeyException(f"Failed to save '{local_path}' in qube '{target_qube.name}'")


def export_submission_pub_key_to_admin(args: argparse.Namespace) -> None:
    print("Updating public key in sd-admin qube...")
    try:
        sd_admin_qube = qubesadmin.Qubes().domains["sd-admin"]
    except QubesException:
        raise SubmissionKeyException(
            "'sd-admin' qube not found! "
            "You need to run `securedrop-manage apply --target admin` first."
        )

    copy_file_to_qube(
        local_path=DOM0_PUB_KEY_PATH,
        target_qube=sd_admin_qube,
        target_path=SD_ADMIN_PUB_KEY_PATH,
        overwrite=args.overwrite,
    )

    print("Public key succesfully exported to 'sd-admin' qube!")

    print(f"Updating site-specific settings in '{SD_ADMIN_SITE_SPECIFIC_PATH}'")
    site_specific_changes = {
        "securedrop_app_gpg_fingerprint": get_submission_key_fingerprint(DOM0_SEC_KEY_PATH),
        "securedrop_app_gpg_public_key": SD_ADMIN_PUB_KEY_PATH,
    }
    try:
        for key, value in site_specific_changes.items():
            sd_admin_qube.run(
                "securedrop-set-site-specific --file "
                + f"{SD_ADMIN_SITE_SPECIFIC_PATH} {key} {value}",
            )
    except subprocess.CalledProcessError as e:
        raise SubmissionKeyException("Failed to update site-specific configurations") from e


def copy_pub_key_to_usb(vm: qubesadmin.vm.QubesVM, overwrite: bool) -> None:
    """
    Ask the user for a folder on the USB drive attached to 'vm', copy the
    public key there and lock the drive
    """
    while True:
        print(f"In '{vm.name}', unlock the drive and choose a folder on it...")
        try:
            stdout, _ = vm.run_service_for_stdio("qubes.SelectDirectory")
        except subprocess.CalledProcessError:
            raise SubmissionKeyException("no folder selected")
        untrusted_directory = stdout.decode("ascii", errors="ignore")
        directory = shlex.quote(untrusted_directory.removesuffix("\n"))
        if directory.startswith(("/media/", "/run/media/")):
            break
        print(f"Selected folder is not on a USB drive: {directory}")
        if input("Pick another folder? [Y/n] ").lower() == "n":
            raise SubmissionKeyException("export cancelled")

    target_path = f"{directory}/{Path(SD_ADMIN_PUB_KEY_FILE_NAME).name}"
    copy_file_to_qube(
        local_path=DOM0_PUB_KEY_PATH,
        target_qube=vm,
        target_path=target_path,
        overwrite=overwrite,
        sudo=True,
    )

    print("Public key successfully exported to USB device")
    try:
        # Unmount the filesystem (optional)
        subprocess.run(
            [
                "qvm-run",
                vm.name,
                f"udisksctl unmount -b $(findmnt -no SOURCE --target {directory})",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("Failed to unmount drive")

    except subprocess.CalledProcessError:
        print(f"{BOLD}{RED}WARNING:{RESET} failed to unmount drive", file=sys.stderr)


def export_submission_pub_key_to_usb(args: argparse.Namespace) -> None:
    app = qubesadmin.Qubes()
    try:
        sd_devices = app.domains["sd-devices"]
    except QubesException:
        raise SubmissionKeyException("'sd-devices' qube not found!")

    # USB drives are automatically attached to sd-devices
    input("Insert the USB drive and press Enter...")
    copy_pub_key_to_usb(sd_devices, args.overwrite)

    print("You can now remove the USB drive.\n")


def export_submission_pub_key(args: argparse.Namespace) -> None:
    use_usb = (
        args.usb
        or not get_installed_product().contains_admin
        or input("Export to [a]dmin qube or [u]sb drive? Please pick [a/u]: ").lower() == "u"
    )
    if use_usb:
        export_submission_pub_key_to_usb(args)
    else:
        export_submission_pub_key_to_admin(args)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage SecureDrop Submission Key")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Key generation
    generate = subparsers.add_parser("generate", help="Generate a new Submission Key")
    generate.set_defaults(run=generate_submission_key)
    generate.add_argument("organization", help="Name of your organization")
    generate.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing Submission Key",
    )

    # Key exporting
    export = subparsers.add_parser("export", help="Export the Submission Key (public key only)")
    export.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing Submission Key",
    )
    export.add_argument(
        "--usb",
        action="store_true",
        help="Export to a USB drive",
    )
    export.set_defaults(run=export_submission_pub_key)

    args = parser.parse_args()

    try:
        args.run(args)
    except SubmissionKeyException as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
