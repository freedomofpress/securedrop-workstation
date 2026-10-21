"""
Integration tests for validating SecureDrop Workstation config,
specifically for the "sd-journalist-vault" VM and related functionality.
"""

import contextlib
import subprocess
from datetime import datetime

import pytest
from qubesadmin.app import VMCollection

from securedrop_manage.config_types import Dom0Config
from tests.base import (
    SD_INBOX_TEMPLATE,
    SD_TAG,
    QubeWrapper,
)
from tests.base import (
    Test_SD_VM_Common as Test_SD_Log_Common,  # noqa: F401 [HACK: import so base tests run]
)

KEEPASS_DB_PATH = "/home/user/journalist-keepassx.kdbx"
CMD_VAULT_SERVICE_STATUS = (
    "sudo systemctl status securedrop-setup-journalist-vault.service --no-pager"
)


@pytest.fixture(scope="module")
def qube() -> QubeWrapper:
    return QubeWrapper("sd-journalist-vault")


def file_created_after_boot(qube: QubeWrapper, file: str) -> bool:
    """Check that a file was since starting the machine"""
    file_creation_time = datetime.fromtimestamp(int(qube.run(f"stat -c %W {KEEPASS_DB_PATH}")))
    boot_time = datetime.fromtimestamp(int(qube.run("awk '/btime/{print $2}' /proc/stat")))
    return file_creation_time > boot_time


@pytest.mark.configuration
def test_journ_vault_package_installed(qube: QubeWrapper) -> None:
    assert qube.package_is_installed("securedrop-vault")


@pytest.mark.configuration
def test_journ_vault_keepassxc_installed(qube: QubeWrapper) -> None:
    assert qube.package_is_installed("keepassxc")


@pytest.mark.run_alone
@pytest.mark.configuration
def test_journ_vault_keepassxc_db_placed(qube: QubeWrapper, token: str) -> None:
    # Remove file from previous failures or system startups
    with contextlib.suppress(subprocess.CalledProcessError):
        # ignore failed removals (it probably didn't exist)
        qube.run(f"rm {KEEPASS_DB_PATH}")
    qube.vm.shutdown(wait=True)

    # Check that file was set up during this boot
    assert qube.fileExists(KEEPASS_DB_PATH)
    assert file_created_after_boot(qube, KEEPASS_DB_PATH)

    # Write something to the file to detect that it survives reboots
    qube.vm.run(f"tee {KEEPASS_DB_PATH}", input=token.encode())
    qube.vm.shutdown(wait=True)

    # Systemd service 'securedrop-setup-journalist-vault' didn't run
    # due to a password database already being present in the right place
    with pytest.raises(subprocess.CalledProcessError) as e:
        qube.run(CMD_VAULT_SERVICE_STATUS)
    assert e.value.returncode == 3  # "innactive"
    assert f"ConditionPathExists=!{KEEPASS_DB_PATH} was not met" in e.value.stdout.decode()

    # KeePass file wasn't overwritten
    assert qube.fileExists(KEEPASS_DB_PATH)
    qube.run(f"cat {KEEPASS_DB_PATH}").strip() == token


@pytest.mark.provisioning
def test_journ_vault_config(
    qube: QubeWrapper, dom0_config: Dom0Config, all_vms: VMCollection
) -> None:
    """
    Confirm that qvm-prefs match expectations for the sd-journalist-vault VM.
    """
    vm = all_vms["sd-journalist-vault"]
    nvm = vm.netvm
    assert nvm is None
    assert vm.template.name == SD_INBOX_TEMPLATE
    assert not vm.autostart
    assert not vm.provides_network
    assert not vm.template_for_dispvms
    assert vm.features["service.paxctld"] == "1"
    assert vm.features["service.securedrop-setup-journalist-vault"] == "1"
    assert not vm.template_for_dispvms
    assert SD_TAG in vm.tags

    # KeePassXC is listed in the menu items
    assert "org.keepassxc.KeePassXC.desktop" in vm.features["menu-items"]
