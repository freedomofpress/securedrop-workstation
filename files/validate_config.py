#!/usr/bin/python3
"""
Utility to verify that SecureDrop Workstation config is properly structured.
Checks for
"""

import json
import os
import re
import subprocess
import sys
import tempfile

from qubesadmin import Qubes

TOR_V3_HOSTNAME_REGEX = r"^[a-z2-7]{56}\.onion$"
TOR_V3_AUTH_REGEX = r"^[A-Z2-7]{52}$"

# CONFIG_FILEPATH = "/srv/salt/securedrop_salt/config.json"
CONFIG_FILEPATH = "config.json"
SECRET_KEY_FILEPATH = "sd-journalist.sec"


class ValidationError(Exception):
    pass


class SDWConfigValidator:
    def __init__(self, config_base_dir=None):
        if config_base_dir:
            self.config_filepath = os.path.join(config_base_dir, CONFIG_FILEPATH)
            self.secret_key_filepath = os.path.join(config_base_dir, SECRET_KEY_FILEPATH)
        else:
            self.config_filepath = CONFIG_FILEPATH
            self.secret_key_filepath = SECRET_KEY_FILEPATH
        self.confirm_config_file_exists()
        self.config = self.read_config_file()
        self.confirm_onion_config_valid()
        self.confirm_submission_privkey_file()
        self.confirm_submission_privkey_fingerprint()
        self.confirm_environment_valid()
        self.validate_existing_size()

    def confirm_config_file_exists(self):
        if not os.path.exists(self.config_filepath):
            raise ValidationError(
                f"Config file does not exist: {self.config_filepath}. "
                "Create from config.json.example"
            )

    def confirm_environment_valid(self):
        """
        The 'environment' config item is required to determine
        whether prod or dev URLs are used for installing packages.
        """
        if "environment" not in self.config:
            raise ValidationError
        if self.config["environment"] not in ("prod", "dev", "staging"):
            raise ValidationError(f"Invalid environment: {self.config['environment']}")

    def confirm_onion_config_valid(self):
        """
        Only v3 onion services are supported.
        """
        if "hidserv" not in self.config:
            raise ValidationError('"hidserv" is not defined in config.json')

        # Verify the hostname
        if "hostname" not in self.config["hidserv"]:
            raise ValidationError("hidden service hostname is not defined in config.json")
        if not re.match(TOR_V3_HOSTNAME_REGEX, self.config["hidserv"]["hostname"]):
            raise ValidationError("Invalid hidden service hostname specified")

        # Verify the key
        if "key" not in self.config["hidserv"]:
            raise ValidationError("hidden service key is not defined in config.json")
        if not re.match(TOR_V3_AUTH_REGEX, self.config["hidserv"]["key"]):
            raise ValidationError("Invalid hidden service key specified")

    def confirm_submission_privkey_file(self):
        """
        Import privkey into temporary keyring, to validate.
        """
        if not os.path.exists(self.secret_key_filepath):
            raise ValidationError(f"PGP secret key file not found: {self.secret_key_filepath}")
        gpg_cmd = ["gpg", "--import", self.secret_key_filepath]
        result = False
        with tempfile.TemporaryDirectory() as d:
            gpg_env = {"GNUPGHOME": d}
            # Call out to gpg to confirm it's a valid keyfile
            try:
                subprocess.check_call(
                    gpg_cmd, env=gpg_env, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
                )
                result = True
            except subprocess.CalledProcessError:
                # suppress error since "result" is checked next
                pass

        if not result:
            raise ValidationError(f"PGP secret key is not valid: {self.secret_key_filepath}")

    def confirm_submission_privkey_fingerprint(self):
        if "submission_key_fpr" not in self.config:
            raise ValidationError('"submission_key_fpr" is not defined in config.json')
        if not re.match("^[a-fA-F0-9]{40}$", self.config["submission_key_fpr"]):
            raise ValidationError("Invalid PGP key fingerprint specified")
        gpg_cmd = ["gpg2", "--show-keys", self.secret_key_filepath]
        try:
            out = subprocess.check_output(gpg_cmd, stderr=subprocess.STDOUT).decode(
                sys.stdout.encoding
            )
            match = "      {}".format(self.config["submission_key_fpr"])
            if not re.search(match, out):
                raise ValidationError("Configured fingerprint does not match key!")

        except subprocess.CalledProcessError as e:
            raise ValidationError(f"Key validation failed: {e.output.decode(sys.stdout.encoding)}")

    def read_config_file(self):
        with open(self.config_filepath) as f:
            return json.load(f)

    def validate_existing_size(self):
        """This method checks for existing private volume size and new
        values in the config.json"""
        if "vmsizes" not in self.config:
            raise ValidationError('Private volume sizes ("vmsizes") are not defined in config.json')
        if "sd_app" not in self.config["vmsizes"]:
            raise ValidationError("Private volume size of sd-app must be defined in config.json")
        if "sd_log" not in self.config["vmsizes"]:
            raise ValidationError("Private volume size of sd-log must be defined in config.json")

        if not isinstance(self.config["vmsizes"]["sd_app"], int):
            raise ValidationError("Private volume size of sd-app must be an integer value.")
        if not isinstance(self.config["vmsizes"]["sd_log"], int):
            raise ValidationError("Private volume size of sd-log must be an integer value.")

        app = Qubes()
        if "sd-app" in app.domains:
            vm = app.domains["sd-app"]
            vol = vm.volumes["private"]
            if not (vol.size <= self.config["vmsizes"]["sd_app"] * 1024 * 1024 * 1024):
                raise ValidationError("sd-app private volume is already bigger than configuration.")

        if "sd-log" in app.domains:
            vm = app.domains["sd-log"]
            vol = vm.volumes["private"]
            if not (vol.size <= self.config["vmsizes"]["sd_log"] * 1024 * 1024 * 1024):
                raise ValidationError("sd-log private volume is already bigger than configuration.")


if __name__ == "__main__":
    validator = SDWConfigValidator()
