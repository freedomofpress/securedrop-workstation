import importlib.machinery
import importlib.util
import json
import os
import warnings
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import dnf
import pytest
import systemd.journal
from qubesadmin import Qubes
from qubesadmin.app import VMCollection
from qubesadmin.vm import QubesVM

from sdw_util.config_types import Dom0Config
from tests.base import (
    CURRENT_FEDORA_TEMPLATE,
    SD_INBOX_TEMPLATE,
    SD_TEMPLATE_BASE,
    SD_VIEWER_TEMPLATE,
    is_workstation_qube,
)


@pytest.fixture(scope="session")
def proj_root() -> os.PathLike[Any]:
    return Path(__file__).parent.parent


@pytest.fixture(autouse=True)
def load_non_standard_module() -> Callable[[os.PathLike[Any]], ModuleType]:
    """
    Fixture factory for loading a non-standard python modules

    This is necessary as a workaround due to the fact that some files not
    following the standard python naming inventions, in particular:
      1. Files ending in '.py'
      2. No dashes ('-') in file names

    Example:

    .. code-block:: python

        @pytest.fixture()
        def custom_module(load_non_standard_module):
            return load_non_standard_module("custom_module", "/usr/bin/custom-module")

        def test_foo(custom_module):
            custom_module.custom_fn()
    """

    def _load_non_standard_module(module_path: os.PathLike) -> ModuleType:
        # Optional: pythonify the module name. In practice this does not matter since
        # the fixture effectively acts as the module reference
        module_name = Path(module_path).stem.replace(".", "_").replace("-", "_")

        # NOTE loader needed since 'importlib.util.spec_from_file_location' only
        # works with '.py' files and RPC service does not have an extension
        loader = importlib.machinery.SourceFileLoader(module_name, str(module_path))
        spec = importlib.util.spec_from_loader(module_name, loader)
        assert spec is not None
        assert spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    return _load_non_standard_module


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
def dom0_config(proj_root: os.PathLike) -> Dom0Config:
    """Make the dom0 "config.json" available to tests."""
    with open(os.path.join(proj_root, "config.json")) as c:
        config = json.load(c)
        # TODO: in the future, when "config.json" does not include an env declaration,
        # If the "environment" key is absent from the "config.json" file, assume prod,
        # as a sane default. Dev environments will have it set explicitly.
        if "environment" not in config:
            warnings.warn("no 'environment' detected in config.json, assuming prod", stacklevel=2)
            config["environment"] = "prod"
    return Dom0Config.parse(config)


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
        SD_VIEWER_TEMPLATE,
        SD_INBOX_TEMPLATE,
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
