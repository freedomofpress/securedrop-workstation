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
