#!/usr/bin/python3
"""
Utility to verify that SecureDrop Workstation config is properly structured.

Structural validation of `config.json` lives in `sdw_util.config_types`; see
`Dom0Config.parse`. The class below additionally cross-checks the config
against on-disk state: the Submission secret key file and existing
private volumes for Qubes AppVMs.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from typing import Any

from qubesadmin import Qubes

from sdw_util.config_types import Dom0Config, ValidationError

# CONFIG_FILEPATH = "/srv/salt/securedrop_salt/config.json"
CONFIG_FILEPATH = "config.json"
SECRET_KEY_FILEPATH = "sd-journalist.sec"

# Re-export for callers that historically imported ValidationError from this module.
__all__ = ["SDWConfigValidator", "ValidationError"]


class SDWConfigValidator:
    def __init__(self, config_base_dir: str | os.PathLike[str] | None = None) -> None:
        if config_base_dir:
            self.config_filepath = os.path.join(config_base_dir, CONFIG_FILEPATH)
            self.secret_key_filepath = os.path.join(config_base_dir, SECRET_KEY_FILEPATH)
        else:
            self.config_filepath = CONFIG_FILEPATH
            self.secret_key_filepath = SECRET_KEY_FILEPATH
        self.confirm_config_file_exists()
        self.config: Dom0Config = Dom0Config.parse(self.read_config_file())
        self.confirm_submission_privkey_file()
        self.confirm_submission_privkey_fingerprint()
        self.validate_existing_size()

    def confirm_config_file_exists(self) -> None:
        if not os.path.exists(self.config_filepath):
            raise ValidationError(
                f"Config file does not exist: {self.config_filepath}. "
                "Create from config.json.example"
            )

    def confirm_submission_privkey_file(self) -> None:
        """
        Import privkey into temporary keyring, to validate.
        """
        if not os.path.exists(self.secret_key_filepath):
            raise ValidationError(f"PGP secret key file not found: {self.secret_key_filepath}")
        with open(self.secret_key_filepath) as f:
            for line in f:
                sline = line.strip()
                if not sline:
                    # Whitespace at top of file
                    continue
                if sline.startswith("-----BEGIN PGP PRIVATE KEY BLOCK-----"):
                    # Good enough; it is imported later to check it's well-formed
                    break
                else:
                    # Expecting a file with an armored secret key only
                    raise ValidationError(
                        "PGP secret key file provided is not an armored private key"
                    )
        gpg_cmd = ["gpg", "--import", self.secret_key_filepath]
        result = False
        with tempfile.TemporaryDirectory() as d:
            gpg_env = {"GNUPGHOME": d}
            # Call out to gpg to confirm it's a valid keyfile
            try:
                subprocess.check_output(gpg_cmd, env=gpg_env, stderr=subprocess.STDOUT)
                result = True
            except subprocess.CalledProcessError as err:
                if err.output and "No pinentry" in err.output.decode():
                    raise ValidationError("PGP key is passphrase-protected.")
                # Otherwise, continue; "result" is checked next
        if not result:
            raise ValidationError(f"PGP secret key is not valid: {self.secret_key_filepath}")

    def confirm_submission_privkey_fingerprint(self) -> None:
        """Cross-check the configured fingerprint against the on-disk key file."""
        gpg_cmd = ["gpg2", "--show-keys", self.secret_key_filepath]
        try:
            out = subprocess.check_output(gpg_cmd, stderr=subprocess.STDOUT).decode(
                sys.stdout.encoding
            )
            match = f"      {self.config.submission_key_fpr}"
            if not re.search(match, out):
                raise ValidationError("Configured fingerprint does not match key!")

        except subprocess.CalledProcessError as e:
            raise ValidationError(f"Key validation failed: {e.output.decode(sys.stdout.encoding)}")

    def read_config_file(self) -> Any:
        with open(self.config_filepath) as f:
            return json.load(f)

    def validate_existing_size(self) -> None:
        """Reject configs that would shrink an existing private volume."""
        app = Qubes()
        if "sd-app" in app.domains:
            vm = app.domains["sd-app"]
            vol = vm.volumes["private"]
            if not (vol.size <= self.config.vmsizes.sd_app * 1024 * 1024 * 1024):
                raise ValidationError("sd-app private volume is already bigger than configuration.")

        if "sd-log" in app.domains:
            vm = app.domains["sd-log"]
            vol = vm.volumes["private"]
            if not (vol.size <= self.config.vmsizes.sd_log * 1024 * 1024 * 1024):
                raise ValidationError("sd-log private volume is already bigger than configuration.")


if __name__ == "__main__":
    validator = SDWConfigValidator()
