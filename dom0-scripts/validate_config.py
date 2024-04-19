#!/usr/bin/env python3
"""
Utility to verify that SecureDrop Workstation config is properly structured.
Checks for
"""
import json
import re
import os
import sys
import subprocess
import tempfile
from qubesadmin import Qubes


TOR_V3_HOSTNAME_REGEX = r"^[a-z2-7]{56}\.onion$"
TOR_V3_AUTH_REGEX = r"^[A-Z2-7]{52}$"

# CONFIG_FILEPATH = "/srv/salt/sd/config.json"
CONFIG_FILEPATH = "config.json"
SECRET_KEY_FILEPATH = "sd-journalist.sec"


class ValidationError(Exception):
    pass


class SDWConfigValidator(object):
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
        try:
            assert os.path.exists(self.config_filepath)
        except AssertionError:
            msg = "Config file does not exist: {}".format(self.config_filepath)
            msg += "Create from config.json.example"
            raise AssertionError(msg)

    def confirm_environment_valid(self):
        """
        The 'environment' config item is required to determine
        whether prod or dev URLs are used for installing packages.
        """
        assert "environment" in self.config
        assert self.config["environment"] in ("prod", "dev", "staging")

    def confirm_onion_config_valid(self):
        """
        Only v3 onion services are supported.
        """
        try:
            self.confirm_onion_v3_url()
            self.confirm_onion_v3_auth()
        except AssertionError:
            print(
                "ERROR: Onion service configuration missing or does not match expected format.\n"
                "Please note that only v3 onion services are supported.\n"
            )
            raise

    def confirm_onion_v3_url(self):
        assert "hidserv" in self.config
        assert "hostname" in self.config["hidserv"]
        assert re.match(TOR_V3_HOSTNAME_REGEX, self.config["hidserv"]["hostname"])

    def confirm_onion_v3_auth(self):
        assert "hidserv" in self.config
        assert "key" in self.config["hidserv"]
        assert re.match(TOR_V3_AUTH_REGEX, self.config["hidserv"]["key"])

    def confirm_submission_privkey_file(self):
        """
        Import privkey into temporary keyring, to validate.
        """
        assert os.path.exists(self.secret_key_filepath)
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
        assert result, "GPG private key is not valid: {}".format(self.secret_key_filepath)

    def confirm_submission_privkey_fingerprint(self):
        assert "submission_key_fpr" in self.config
        assert re.match("^[a-fA-F0-9]{40}$", self.config["submission_key_fpr"])
        gpg_cmd = ["gpg2", "--show-keys", self.secret_key_filepath]
        try:
            out = subprocess.check_output(gpg_cmd, stderr=subprocess.STDOUT).decode(
                sys.stdout.encoding
            )
            match = "      {}".format(self.config["submission_key_fpr"])
            assert re.search(match, out), "Configured fingerprint does not match key!"

        except subprocess.CalledProcessError as e:
            assert False, "Key validation failed: {}".format(e.output.decode(sys.stdout.encoding))

    def read_config_file(self):
        with open(self.config_filepath, "r") as f:
            j = json.load(f)
        return j

    def validate_existing_size(self):
        """This method checks for existing private volume size and new
        values in the config.json"""
        assert "vmsizes" in self.config
        assert "sd_app" in self.config["vmsizes"]
        assert "sd_log" in self.config["vmsizes"]

        assert isinstance(
            self.config["vmsizes"]["sd_app"], int
        ), "Private volume size of sd-app must be an integer value."
        assert isinstance(
            self.config["vmsizes"]["sd_log"], int
        ), "Private volume size of sd-log must be an integer value."

        app = Qubes()
        if "sd-app" in app.domains:
            vm = app.domains["sd-app"]
            vol = vm.volumes["private"]
            assert (
                vol.size <= self.config["vmsizes"]["sd_app"] * 1024 * 1024 * 1024
            ), "sd-app private volume is already bigger than configuration."

        if "sd-log" in app.domains:
            vm = app.domains["sd-log"]
            vol = vm.volumes["private"]
            assert (
                vol.size <= self.config["vmsizes"]["sd_log"] * 1024 * 1024 * 1024
            ), "sd-log private volume is already bigger than configuration."


if __name__ == "__main__":
    validator = SDWConfigValidator()
