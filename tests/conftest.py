import json
import os
import warnings
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import cast

import dnf
import pytest
import systemd.journal
from qubesadmin import Qubes
from qubesadmin.app import VMCollection
from qubesadmin.vm import QubesVM

from sdw_util.config_types import Dom0Config
from tests.base import (
    CURRENT_FEDORA_TEMPLATE,
    SD_TEMPLATE_BASE,
    SD_TEMPLATE_LARGE,
    SD_TEMPLATE_SMALL,
    is_workstation_qube,
)

PROJ_ROOT = Path(__file__).parent.parent

skip_on_qubes_4_2 = pytest.mark.skipif(
    dnf.rpm.detect_releasever("/") == "4.2", reason="Feature only available in Qubes >= 4.3"
)


@pytest.fixture
def qubes_ver() -> str:
    return dnf.rpm.detect_releasever("/")


@pytest.fixture(scope="session")
def mock_block_device(all_vms: VMCollection, worker_id: str, testrun_uid: str) -> Iterator[str]:
    """
    Creates a block device, exposed by sys-usb

    Useful for testing device attachment logic.
    """
    backend_qube = all_vms["sys-usb"]

    # Create file-backed device unique to workers to avoid xdist conflicts
    mock_device_path = f"/tmp/{worker_id}-{testrun_uid}.img"
    backend_qube.run(f"touch {mock_device_path}")
    backend_qube.run(f"sudo losetup -f {mock_device_path}")

    # Obtain path of newly created device. QubesVM.run() returns (stdout, stderr)
    # as bytes, so unwrap to str. Format of stdout: "/dev/loopX\n".
    cmd_get_device_path = f"losetup --associated {mock_device_path} --output NAME --noheadings"
    device_path = backend_qube.run(cmd_get_device_path)[0].decode().strip()

    # Return qvm-block format: BACKEND:DEVID
    yield f"{backend_qube.name}:{device_path.removeprefix('/dev/')}"

    # Remove device
    backend_qube.run(f"sudo losetup -d {device_path}")


@pytest.fixture(scope="session")
def dom0_config() -> Dom0Config:
    """Make the dom0 "config.json" available to tests."""
    with open(os.path.join(PROJ_ROOT, "config.json")) as c:
        config = json.load(c)
        # TODO: in the future, when "config.json" does not include an env declaration,
        # If the "environment" key is absent from the "config.json" file, assume prod,
        # as a sane default. Dev environments will have it set explicitly.
        if "environment" not in config:
            warnings.warn("no 'environment' detected in config.json, assuming prod", stacklevel=2)
            config["environment"] = "prod"
    # Trust validate_config.py to have rejected malformed configs upstream of test runs.
    return cast(Dom0Config, config)


@pytest.fixture(scope="session")
def all_vms() -> VMCollection:
    """Obtain all qubes present in the system"""
    return Qubes().domains


@pytest.fixture(scope="session")
def sdw_tagged_vms(all_vms: VMCollection) -> list[QubesVM]:
    """Obtain all SecureDrop Workstation-exclusive qubes"""
    return list(filter(is_workstation_qube, all_vms))


@pytest.fixture(scope="session", autouse=True)
def cleanup(request: pytest.FixtureRequest, sdw_tagged_vms: list[QubesVM]) -> Iterator[None]:
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
def qubesd_log() -> Iterator[str]:
    # Obtain journal entries to dig down into expected Qubes-daemon error
    journal = systemd.journal.Reader()
    journal.add_match(_SYSTEMD_UNIT="qubesd.service")
    journal.seek_realtime(datetime.now())

    def _entry_generator(journal: systemd.journal.Reader) -> Iterator[str]:
        for entry in journal:
            yield entry.get("MESSAGE")

    return _entry_generator(journal)
