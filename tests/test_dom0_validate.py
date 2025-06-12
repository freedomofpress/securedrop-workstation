import shutil
import tempfile
import unittest
from pathlib import Path

import pytest

from files.validate_config import SDWConfigValidator, ValidationError


class SD_Dom0_Validate_Tests(unittest.TestCase):
    def setUp(self):
        # Enable full diff output in test report, to aid in debugging
        self.maxDiff = None
        self.test_resources = Path(__file__).parent.resolve()

    def test_good_config(self):
        with tempfile.TemporaryDirectory() as dir:
            shutil.copy(f"{self.test_resources}/files/testconfig.json", f"{dir}/config.json")
            shutil.copy(f"{self.test_resources}/files/example_key.asc", f"{dir}/sd-journalist.sec")

            # Validator currently runs checks in constructor
            SDWConfigValidator(dir)

    def test_missing_config(self):
        with tempfile.TemporaryDirectory() as dir:
            with pytest.raises(ValidationError) as exc_info:
                SDWConfigValidator(dir)

            assert "Config file does not exist" in exc_info.exconly()

    def test_config_malformed_key(self):
        with tempfile.TemporaryDirectory() as dir:
            shutil.copy(f"{self.test_resources}/files/testconfig.json", f"{dir}/config.json")
            shutil.copy(
                f"{self.test_resources}/files/example_key.asc.malformed", f"{dir}/sd-journalist.sec"
            )

            with pytest.raises(ValidationError) as exc_info:
                SDWConfigValidator(dir)

            assert (
                "PGP secret key file provided is not an armored private key" in exc_info.exconly()
            )

    def test_config_malformed_onion_json(self):
        with tempfile.TemporaryDirectory() as dir:
            shutil.copy(
                f"{self.test_resources}/files/testconfig.json.malformedonion", f"{dir}/config.json"
            )
            shutil.copy(f"{self.test_resources}/files/example_key.asc", f"{dir}/sd-journalist.sec")

            with pytest.raises(ValidationError) as exc_info:
                SDWConfigValidator(dir)

            assert "Invalid hidden service hostname specified" in exc_info.exconly()

    def test_config_malformed_fpr_json(self):
        with tempfile.TemporaryDirectory() as dir:
            shutil.copy(
                f"{self.test_resources}/files/testconfig.json.malformedfpr", f"{dir}/config.json"
            )
            shutil.copy(f"{self.test_resources}/files/example_key.asc", f"{dir}/sd-journalist.sec")

            with pytest.raises(ValidationError) as exc_info:
                SDWConfigValidator(dir)

            assert "Invalid PGP key fingerprint specified" in exc_info.exconly()
