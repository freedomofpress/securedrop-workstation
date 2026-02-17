import json
import os
from pathlib import Path

import pytest
from qubesadmin import Qubes

from tests.base import (
    CURRENT_FEDORA_TEMPLATE,
    SD_TEMPLATE_BASE,
    SD_TEMPLATE_LARGE,
    SD_TEMPLATE_SMALL,
    is_workstation_qube,
)

PROJ_ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def dom0_config():
    """Make the dom0 "config.json" available to tests."""
    with open(os.path.join(PROJ_ROOT, "config.json")) as c:
        config = json.load(c)
        # TODO: in the future, when "config.json" does not include an env declaration,
        # If the "environment" key is absent from the "config.json" file, assume prod,
        # as a sane default. Dev environments will have it set explicitly.
        if "environment" not in config:
            pytest.warn("no 'environment' detected in config.json, assuming prod")
            config["environment"] = "prod"
    return config


@pytest.fixture(scope="session")
def all_vms():
    """Obtain all qubes present in the system"""
    return Qubes().domains


@pytest.fixture(scope="session")
def sdw_tagged_vms(all_vms):
    """Obtain all SecureDrop Workstation-exclusive qubes"""
    return list(filter(is_workstation_qube, all_vms))


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
