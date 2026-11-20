"""
Integration tests for validating SecureDrop Workstation config,
specifically for the vault VMs ("sd-journalist-vault" and "sd-admin-vault")
and related functionality.
"""

import contextlib
import subprocess
from datetime import datetime

import pytest
from qubesadmin.app import VMCollection

from tests.base import (
    SD_ADMIN_TEMPLATE,
    SD_INBOX_TEMPLATE,
    SD_TAG,
    QubeWrapper,
)
from tests.base import (
    Test_SD_VM_Common as Test_SD_Vault_Common,  # noqa: F401 [HACK: import so base tests run]
)

# Only what can't be derived from the vault kind ("journalist" or "admin")
TEMPLATES = {"journalist": SD_INBOX_TEMPLATE, "admin": SD_ADMIN_TEMPLATE}
PACKAGES = {"journalist": "securedrop-vault", "admin": "securedrop-admin-qubes"}


@pytest.fixture(scope="module", params=["journalist", "admin"])
def kind(request: pytest.FixtureRequest) -> str:
    # Skip unless the relevant product is installed
    request.getfixturevalue(f"needs_{request.param}")
    return request.param


@pytest.fixture(scope="module")
def qube(kind: str) -> QubeWrapper:
    return QubeWrapper(f"sd-{kind}-vault")


def file_created_after_boot(qube: QubeWrapper, file: str) -> bool:
    """Check that a file was created since starting the machine"""
    file_creation_time = datetime.fromtimestamp(int(qube.run(f"stat -c %W {file}")))
    boot_time = datetime.fromtimestamp(int(qube.run("awk '/btime/{print $2}' /proc/stat")))
    return file_creation_time > boot_time


@pytest.mark.configuration
def test_vault_package_installed(qube: QubeWrapper, kind: str) -> None:
    assert qube.package_is_installed(PACKAGES[kind])


@pytest.mark.configuration
def test_vault_keepassxc_installed(qube: QubeWrapper) -> None:
    assert qube.package_is_installed("keepassxc-minimal")


@pytest.mark.run_alone
@pytest.mark.configuration
def test_vault_keepassxc_db_placed(qube: QubeWrapper, kind: str, token: str) -> None:
    db_path = f"/home/user/Persistent/{kind}.kdbx"

    # Remove file from previous failures or system startups
    with contextlib.suppress(subprocess.CalledProcessError):
        # ignore failed removals (it probably didn't exist)
        qube.run(f"rm {db_path}")
    qube.vm.shutdown(wait=True)

    # Check that file was set up during this boot
    assert qube.fileExists(db_path)
    assert file_created_after_boot(qube, db_path)

    # Write something to the file to detect that it survives reboots
    qube.vm.run(f"tee {db_path}", input=token.encode())
    qube.vm.shutdown(wait=True)

    # Setup systemd service didn't run due to a password database
    # already being present in the right place
    with pytest.raises(subprocess.CalledProcessError) as e:
        qube.run(f"sudo systemctl status securedrop-setup-{kind}-vault.service --no-pager")
    assert e.value.returncode == 3  # "inactive"
    assert f"ConditionPathExists=!{db_path} was not met" in e.value.stdout.decode()

    # KeePass file wasn't overwritten
    assert qube.fileExists(db_path)
    assert qube.run(f"cat {db_path}").strip() == token


@pytest.mark.provisioning
def test_vault_config(kind: str, all_vms: VMCollection) -> None:
    """
    Confirm that qvm-prefs match expectations for the vault VM.
    """
    vm = all_vms[f"sd-{kind}-vault"]
    assert vm.netvm is None
    assert vm.template.name == TEMPLATES[kind]
    assert not vm.autostart
    assert not vm.provides_network
    assert not vm.template_for_dispvms
    assert vm.features["service.paxctld"] == "1"
    assert vm.features[f"service.securedrop-setup-{kind}-vault"] == "1"
    assert SD_TAG in vm.tags
    assert f"sd-{kind}" in vm.tags

    # KeePassXC is listed in the menu items
    assert "org.keepassxc.KeePassXC.desktop" in vm.features["menu-items"]
