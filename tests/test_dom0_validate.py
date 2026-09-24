import shutil
from pathlib import Path

import pytest

from securedrop_manage.config_types import ValidationError
from securedrop_manage.validate import AdminConfigValidator, SDWConfigValidator


@pytest.fixture
def test_resources_dir() -> Path:
    """
    Return path to directory hard-coded test data files.
    """
    return Path(__file__).parent.resolve() / "files"


def test_good_config(test_resources_dir: Path, tmp_path: Path) -> None:
    shutil.copy(f"{test_resources_dir}/testconfig.json", f"{tmp_path}/config.json")
    shutil.copy(f"{test_resources_dir}/example_key.asc", f"{tmp_path}/sd-journalist.sec")

    # Validator currently runs checks in constructor
    SDWConfigValidator(tmp_path)


def test_missing_config(tmp_path: Path) -> None:
    with pytest.raises(ValidationError) as exc_info:
        SDWConfigValidator(tmp_path)

    assert "Config file does not exist" in exc_info.exconly()


def test_config_malformed_key(test_resources_dir: Path, tmp_path: Path) -> None:
    shutil.copy(f"{test_resources_dir}/testconfig.json", f"{tmp_path}/config.json")
    shutil.copy(f"{test_resources_dir}/example_key.asc.malformed", f"{tmp_path}/sd-journalist.sec")

    with pytest.raises(ValidationError) as exc_info:
        SDWConfigValidator(tmp_path)

    assert "PGP secret key file provided is not an armored private key" in exc_info.exconly()


def test_config_malformed_onion_json(test_resources_dir: Path, tmp_path: Path) -> None:
    shutil.copy(f"{test_resources_dir}/testconfig.json.malformedonion", f"{tmp_path}/config.json")
    shutil.copy(f"{test_resources_dir}/example_key.asc", f"{tmp_path}/sd-journalist.sec")

    with pytest.raises(ValidationError) as exc_info:
        SDWConfigValidator(tmp_path)

    assert "Invalid hidden service hostname specified" in exc_info.exconly()


def test_config_malformed_fpr_json(test_resources_dir: Path, tmp_path: Path) -> None:
    shutil.copy(f"{test_resources_dir}/testconfig.json.malformedfpr", f"{tmp_path}/config.json")
    shutil.copy(f"{test_resources_dir}/example_key.asc", f"{tmp_path}/sd-journalist.sec")

    with pytest.raises(ValidationError) as exc_info:
        SDWConfigValidator(tmp_path)

    assert "Invalid PGP key fingerprint specified" in exc_info.exconly()


def test_config_mismatched_fpr(test_resources_dir: Path, tmp_path: Path) -> None:
    """A well-formed but wrong fingerprint must be rejected against the on-disk key."""
    shutil.copy(f"{test_resources_dir}/testconfig.json.mismatched_fpr", f"{tmp_path}/config.json")
    shutil.copy(f"{test_resources_dir}/example_key.asc", f"{tmp_path}/sd-journalist.sec")

    with pytest.raises(ValidationError) as exc_info:
        SDWConfigValidator(tmp_path)

    assert "Configured fingerprint does not match key!" in exc_info.exconly()


def test_admin_good_config(test_resources_dir: Path, tmp_path: Path) -> None:
    # No submission key needed for the admin workstation
    shutil.copy(f"{test_resources_dir}/testconfig.json", f"{tmp_path}/config.json")

    assert AdminConfigValidator(tmp_path).config.environment == "prod"


def test_admin_missing_config(tmp_path: Path) -> None:
    # config.json is optional, defaulting to prod
    assert AdminConfigValidator(tmp_path).config.environment == "prod"


def test_admin_invalid_environment(test_resources_dir: Path, tmp_path: Path) -> None:
    shutil.copy(
        f"{test_resources_dir}/testconfig.json.invalid_environment", f"{tmp_path}/config.json"
    )

    with pytest.raises(ValidationError) as exc_info:
        AdminConfigValidator(tmp_path)

    assert "Invalid environment: production" in exc_info.exconly()
