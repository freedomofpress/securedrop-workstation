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
    """Obtain all qubes present in the system"""
    return Qubes().domains


@pytest.fixture
def sdw_tagged_vms(all_vms):
    """Obtain all SecureDrop Workstation-exclusive qubes"""

    sdw_vms = [vm for vm in all_vms if SD_TAG in vm.tags]
    # filter out the "sd-viewer-disposable" VM, which is an ephemeral DispVM,
    # which will exist at certain points of the test suite
    return [vm for vm in sdw_vms if vm.name != "sd-viewer-disposable"]


@pytest.fixture
def config():
    with open("config.json") as c:
        config = json.load(c)
    if "environment" not in config:
        config["environment"] = "dev"
    return config
