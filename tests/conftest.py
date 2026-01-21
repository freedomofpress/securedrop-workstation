import json
import os
from pathlib import Path

import pytest
from qubesadmin import Qubes

from tests.base import (
    CURRENT_FEDORA_TEMPLATE,
    SD_TAG,
    SD_TEMPLATE_BASE,
    SD_TEMPLATE_LARGE,
    SD_TEMPLATE_SMALL,
)

PROJ_ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def dom0_config():
    """Make the dom0 "config.json" available to tests."""
    with open(os.path.join(PROJ_ROOT, "config.json")) as c:
        config = json.load(c)
        # TODO: in the future, when "config.json" does not include an env declaration,
        # we should either assume "prod" or else infer the env from the keyring
        # packages that are installed. See the `_get_env_by_package` function
        # elsewhere in this test suite for details.
        if "environment" not in config:
            config["environment"] = "dev"
    return config


@pytest.fixture(scope="session")
def all_vms():
    """Obtain all qubes present in the system"""
    return Qubes().domains


@pytest.fixture(scope="session")
def sdw_tagged_vms(all_vms):
    """Obtain all SecureDrop Workstation-exclusive qubes"""

    sdw_vms = [vm for vm in all_vms if SD_TAG in vm.tags]
    # filter out the "sd-viewer-disposable" VM, which is an ephemeral DispVM,
    # which will exist at certain points of the test suite
    return [vm for vm in sdw_vms if vm.name != "sd-viewer-disposable"]


@pytest.fixture(scope="session", autouse=True)
def cleanup(request, sdw_tagged_vms):
    """
    Handles all post-test teardown logic. Mostly that's just shutting down TemplateVMs
    that may have been booted to inspect package state.
    """
    # Yield to wait for test execution to finish
    yield

    # After test suite finishes, run teardown logic.
    app = Qubes()
    for vm_name in [
        SD_TEMPLATE_BASE,
        SD_TEMPLATE_LARGE,
        SD_TEMPLATE_SMALL,
        CURRENT_FEDORA_TEMPLATE,
    ]:
        try:
            vm = app.domains[vm_name]
            if vm.is_running():
                vm.shutdown()
        except KeyError:
            pass
