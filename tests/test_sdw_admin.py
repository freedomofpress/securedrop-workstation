from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest


@pytest.fixture
def sdw_admin(
    proj_root: Path,
    load_non_standard_module: Callable[[Path], ModuleType],
) -> ModuleType:
    """
    Equivalent to 'import sdw_admin', except as a pytest fixture.

    Workaround needed due to 'sdw-admin.py' having a non-pythonic '-' in its
    name and also not currently being in its own python module.
    """

    # FIXME this is a workaroud. A better approach is to have sdw-admin in
    # a proper python module, trivially importable in tests. See #1750.
    return load_non_standard_module(proj_root / "files" / "sdw-admin.py")


def test_is_managed(sdw_admin: ModuleType) -> None:
    assert sdw_admin.is_managed("sd-app")


def test_legacy_config_is_migrated(sdw_admin: ModuleType, tmp_path: Path) -> None:
    CONFIG_PATH: Path = tmp_path / "new_config"
    LEGACY_CONFIG_PATH: Path = tmp_path / "old_config"

    CONFIG_PATH.mkdir()
    LEGACY_CONFIG_PATH.mkdir()

    config_file: Path = LEGACY_CONFIG_PATH / "config.json"
    key_file: Path = LEGACY_CONFIG_PATH / "sd-journalist.sec"
    dummy_file: Path = LEGACY_CONFIG_PATH / "nocopy.txt"

    new_config_file: Path = CONFIG_PATH / "config.json"
    new_key_file: Path = CONFIG_PATH / "sd-journalist.sec"
    new_dummy_file: Path = CONFIG_PATH / "nocopy.txt"

    for source_file in [config_file, key_file, dummy_file]:
        source_file.write_text(str(source_file))

    sdw_admin.move_legacy_config(LEGACY_CONFIG_PATH, CONFIG_PATH)

    # config files should be moved
    for source_file in [config_file, key_file]:
        assert not source_file.exists()

    # other files should not be moved
    assert dummy_file.exists()

    # only the config files should be present in new location
    for source_file in [new_config_file, new_key_file]:
        assert source_file.exists()

    # other files should not be moved
    assert not new_dummy_file.exists()
