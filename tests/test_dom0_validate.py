import shutil
from pathlib import Path

import pytest

from files.validate_config import SDWConfigValidator, ValidationError


@pytest.fixture
def test_resources_dir():
    """
    Return path to directory hard-coded test data files.
    """
    return Path(__file__).parent.resolve() / "files"


def test_good_config(test_resources_dir, tmpdir):
    shutil.copy(f"{test_resources_dir}/testconfig.json", f"{tmpdir}/config.json")
    shutil.copy(f"{test_resources_dir}/example_key.asc", f"{tmpdir}/sd-journalist.sec")

    # Validator currently runs checks in constructor
    SDWConfigValidator(tmpdir)


def test_missing_config(tmpdir):
    with pytest.raises(ValidationError) as exc_info:
        SDWConfigValidator(tmpdir)

    assert "Config file does not exist" in exc_info.exconly()


def test_config_malformed_key(test_resources_dir, tmpdir):
    shutil.copy(f"{test_resources_dir}/testconfig.json", f"{tmpdir}/config.json")
    shutil.copy(f"{test_resources_dir}/example_key.asc.malformed", f"{tmpdir}/sd-journalist.sec")

    with pytest.raises(ValidationError) as exc_info:
        SDWConfigValidator(tmpdir)

    assert "PGP secret key file provided is not an armored private key" in exc_info.exconly()


def test_config_malformed_onion_json(test_resources_dir, tmpdir):
    shutil.copy(f"{test_resources_dir}/testconfig.json.malformedonion", f"{tmpdir}/config.json")
    shutil.copy(f"{test_resources_dir}/example_key.asc", f"{tmpdir}/sd-journalist.sec")

    with pytest.raises(ValidationError) as exc_info:
        SDWConfigValidator(tmpdir)

    assert "Invalid hidden service hostname specified" in exc_info.exconly()


def test_config_malformed_fpr_json(test_resources_dir, tmpdir):
    shutil.copy(f"{test_resources_dir}/testconfig.json.malformedfpr", f"{tmpdir}/config.json")
    shutil.copy(f"{test_resources_dir}/example_key.asc", f"{tmpdir}/sd-journalist.sec")

    with pytest.raises(ValidationError) as exc_info:
        SDWConfigValidator(tmpdir)

    assert "Invalid PGP key fingerprint specified" in exc_info.exconly()
