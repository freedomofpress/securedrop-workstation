import json
from pathlib import Path

import pytest
from qubesadmin import Qubes

from tests.base import SD_TAG

PROJ_ROOT = Path(__file__).parent.parent


@pytest.fixture
def dom0_config():
    """Make the dom0 "config.json" available to tests."""
    with open(PROJ_ROOT / "config.json") as config_file:
        return json.load(config_file)


@pytest.fixture
def all_vms():
    """Obtain all SecureDrop Workstation-exclusive qubes"""
    return Qubes().domains


@pytest.fixture
def sdw_tagged_vms(all_vms):
    """Obtain all SecureDrop Workstation-exclusive qubes"""
    return [vm for vm in all_vms if SD_TAG in vm.tags]


@pytest.fixture
def config():
    with open("config.json") as c:
        config = json.load(c)
    if "environment" not in config:
        config["environment"] = "dev"
    return config
