import json
from pathlib import Path

import pytest

PROJ_ROOT = Path(__file__).parent.parent


@pytest.fixture()
def dom0_config():
    """Make the dom0 "config.json" available to tests."""
    with open(PROJ_ROOT / "config.json") as config_file:
        return json.load(config_file)


@pytest.fixture()
def qube():  # noqa: PT004
    raise NotImplementedError("Implemented by specific test modules")
