import shutil
from pathlib import Path

import pytest

from securedrop_manage.config_types import ValidationError
from securedrop_manage.validate import AdminConfigValidator, JournalistConfigValidator
from tests.markers import needs_dom0


@pytest.fixture
def resources_dir() -> Path:
    """
    Return path to directory hard-coded test data files.
    """
    return Path(__file__).parent.resolve() / "files"


@needs_dom0
def test_good_config(resources_dir: Path, tmp_path: Path) -> None:
    shutil.copy(f"{resources_dir}/testconfig.json", f"{tmp_path}/config.json")
    shutil.copy(f"{resources_dir}/example_key.asc", f"{tmp_path}/sd-journalist.sec")

    # Validator currently runs checks in constructor
    JournalistConfigValidator(tmp_path)


def test_missing_config(tmp_path: Path) -> None:
    with pytest.raises(ValidationError) as exc_info:
        JournalistConfigValidator(tmp_path)

    assert "Config file does not exist" in exc_info.exconly()


def test_config_malformed_key(resources_dir: Path, tmp_path: Path) -> None:
    shutil.copy(f"{resources_dir}/testconfig.json", f"{tmp_path}/config.json")
    shutil.copy(f"{resources_dir}/example_key.asc.malformed", f"{tmp_path}/sd-journalist.sec")

    with pytest.raises(ValidationError) as exc_info:
        JournalistConfigValidator(tmp_path)

    assert "PGP secret key file provided is not an armored private key" in exc_info.exconly()


def test_config_malformed_onion_json(resources_dir: Path, tmp_path: Path) -> None:
    shutil.copy(f"{resources_dir}/testconfig.json.malformedonion", f"{tmp_path}/config.json")
    shutil.copy(f"{resources_dir}/example_key.asc", f"{tmp_path}/sd-journalist.sec")

    with pytest.raises(ValidationError) as exc_info:
        JournalistConfigValidator(tmp_path)

    assert "Invalid hidden service hostname specified" in exc_info.exconly()


def test_config_malformed_fpr_json(resources_dir: Path, tmp_path: Path) -> None:
    shutil.copy(f"{resources_dir}/testconfig.json.malformedfpr", f"{tmp_path}/config.json")
    shutil.copy(f"{resources_dir}/example_key.asc", f"{tmp_path}/sd-journalist.sec")

    with pytest.raises(ValidationError) as exc_info:
        JournalistConfigValidator(tmp_path)

    assert "Invalid PGP key fingerprint specified" in exc_info.exconly()


def test_config_mismatched_fpr(resources_dir: Path, tmp_path: Path) -> None:
    """A well-formed but wrong fingerprint must be rejected against the on-disk key."""
    shutil.copy(f"{resources_dir}/testconfig.json.mismatched_fpr", f"{tmp_path}/config.json")
    shutil.copy(f"{resources_dir}/example_key.asc", f"{tmp_path}/sd-journalist.sec")

    with pytest.raises(ValidationError) as exc_info:
        JournalistConfigValidator(tmp_path)

    assert "Configured fingerprint does not match key!" in exc_info.exconly()


def test_admin_good_config(resources_dir: Path, tmp_path: Path) -> None:
    # No submission key needed for the admin workstation
    shutil.copy(f"{resources_dir}/testconfig.json", f"{tmp_path}/config.json")

    assert AdminConfigValidator(tmp_path).config.environment == "prod"


def test_admin_missing_config(tmp_path: Path) -> None:
    # config.json is optional, defaulting to prod
    assert AdminConfigValidator(tmp_path).config.environment == "prod"


def test_admin_invalid_environment(resources_dir: Path, tmp_path: Path) -> None:
    shutil.copy(f"{resources_dir}/testconfig.json.invalid_environment", f"{tmp_path}/config.json")

    with pytest.raises(ValidationError) as exc_info:
        AdminConfigValidator(tmp_path)

    assert "Invalid environment: production" in exc_info.exconly()
