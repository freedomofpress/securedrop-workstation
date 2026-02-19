import json
import os
from datetime import datetime
from pathlib import Path

import pytest
import systemd.journal
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
def mock_block_device(all_vms, worker_id, testrun_uid):
    """
    Creates a block device, exposed by sys-usb

    Useful for testing device attachment logic.
    """
    backend_qube = all_vms["sys-usb"]

    # Create file-backed device unique to workers to avoid xdist conflicts
    mock_device_path = f"/tmp/{worker_id}-{testrun_uid}.img"
    backend_qube.run(f"touch {mock_device_path}")
    backend_qube.run(f"sudo losetup -f {mock_device_path}")

    # Obtain path of newly created device
    cmd_get_device_path = f"losetup --associated {mock_device_path} --output NAME --noheadings"
    device_path = backend_qube.run(cmd_get_device_path)[0].decode().strip()  # format: /dev/loopX

    # Return qvm-block format: BACKEND:DEVID
    yield f"{backend_qube.name}:{device_path.strip('/dev/')}"

    # Remove device
    backend_qube.run(f"sudo losetup -d {device_path}")


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


@pytest.fixture
def qubesd_log():
    # Obtain journal entries to dig down into expected Qubes-daemon error
    journal = systemd.journal.Reader()
    journal.add_match(_SYSTEMD_UNIT="qubesd.service")
    journal.seek_realtime(datetime.now())

    def _entry_generator(journal):
        for entry in journal:
            yield entry.get("MESSAGE")

    return _entry_generator(journal)
