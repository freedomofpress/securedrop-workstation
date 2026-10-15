#!/usr/bin/python3
"""
Generate a new Submission Key in dom0 and export the fingerprint, secret and public keys
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

# XDG_CONFIG_HOME is not set in 4.3 Qubes - set it manually
CONFIG_DIR = Path.home() / ".config/securedrop-manage"
SECRET_KEY_PATH = CONFIG_DIR / "sd-journalist.sec"
PUBLIC_KEY_PATH = CONFIG_DIR / "sd-journalist.pub"
CONFIG_PATH = CONFIG_DIR / "config.json"


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a new Submission Key")
    parser.add_argument("organization", help="Name of your organization")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing Submission Key",
    )
    args = parser.parse_args()

    if SECRET_KEY_PATH.exists() and not args.overwrite:
        print(
            f"Error: a submission key already exists at {SECRET_KEY_PATH}. "
            "Use --overwrite to overwrite it.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Generating submission key...")
    fingerprint, secret_key, public_key = generate_key(args.organization)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    write_private(SECRET_KEY_PATH, secret_key)
    PUBLIC_KEY_PATH.write_text(public_key)

    # Edit or create config.json and set submission_key_fpr
    config = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    config["submission_key_fpr"] = fingerprint
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")

    print(f"Generated Submission Key with fingerprint: {fingerprint}")
    print(f"Secret key is saved to: {SECRET_KEY_PATH}")
    print(f"Public key is saved to: {PUBLIC_KEY_PATH}")


if __name__ == "__main__":
    main()
