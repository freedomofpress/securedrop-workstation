import pytest

from . import (
    QubeWrapper,
    Test_SD_VM_Local,  # noqa: F401 [HACK: import so base tests run]
)


@pytest.fixture()
def whonix_apt_list():
    return "/etc/apt/sources.list.d/derivative.list"


@pytest.fixture(scope="module")
def qube():
    return QubeWrapper("sd-whonix", expected_config_keys={"SD_HIDSERV_HOSTNAME", "SD_HIDSERV_KEY"})


def test_sd_whonix_config_enabled(qube):
    assert qube.qubes_service_enabled("securedrop-whonix-config")


def test_sd_whonix_config(qube, dom0_config):
    assert dom0_config["hidserv"]["hostname"] == qube.vm_config_read("SD_HIDSERV_HOSTNAME")
    assert dom0_config["hidserv"]["key"] == qube.vm_config_read("SD_HIDSERV_KEY")


def test_v3_auth_private_file(qube):
    hidserv_hostname = qube.vm_config_read("SD_HIDSERV_HOSTNAME")
    hidserv_key = qube.vm_config_read("SD_HIDSERV_KEY")
    line = f"{hidserv_hostname}:descriptor:x25519:{hidserv_key}"

    qube.assertFileHasLine("/var/lib/tor/authdir/app-journalist.auth_private", line)


def test_sd_whonix_repo_enabled(qube, whonix_apt_list):
    """
    During Whonix 14 -> 15 migration, we removed the apt list file
    (because the repo wasn't serving, due to EOL status). Let's
    make sure it's there, since we're past 14 now.
    """
    assert qube.fileExists(whonix_apt_list)


def test_sd_whonix_verify_tor_config(qube):
    # User must be debian-tor for v3 Onion, due to restrictive
    # mode on the client keys directory.
    qube.run("tor --verify-config", user="debian-tor")


def test_whonix_torrc(qube):
    """
    Ensure Whonix-maintained torrc files don't contain duplicate entries.
    """
    torrc_contents = qube.get_file_contents("/etc/tor/torrc")
    duplicate_includes = """%include /etc/torrc.d/
%include /etc/torrc.d/95_whonix.conf"""
    assert (
        duplicate_includes not in torrc_contents
    ), r"Whonix GW torrc contains duplicate %\include lines"
