import pytest

from . import (
    QubeWrapper,
    Test_SD_VM_Local,  # noqa: F401 [HACK: import so base tests run]
)


@pytest.fixture(scope="module")
def qube():
    return QubeWrapper(
        "sd-app",
        expected_config_keys={
            "QUBES_GPG_DOMAIN",
            "SD_SUBMISSION_KEY_FPR",
            "SD_MIME_HANDLING",
        },
        enforced_apparmor_profiles={
            "/usr/bin/securedrop-client",
        },
    )


def test_open_in_dvm_desktop(qube):
    contents = qube.get_file_contents("/usr/share/applications/open-in-dvm.desktop")
    expected_contents = [
        "TryExec=/usr/bin/qvm-open-in-vm",
        "Exec=/usr/bin/qvm-open-in-vm --view-only @dispvm:sd-viewer %f",
    ]
    for line in expected_contents:
        assert line in contents


def test_mimeapps(qube):
    results = qube.run("cat /usr/share/applications/mimeapps.list")
    for line in results.splitlines():
        if line.startswith(("#", "[Default")):
            # Skip comments and the leading [Default Applications]
            continue
        mime, target = line.split("=", 1)
        assert target == "open-in-dvm.desktop;"
        # Now functionally test it
        actual_app = qube.run(f"xdg-mime query default {mime}")
        assert actual_app == "open-in-dvm.desktop"


def test_mailcap_hardened(qube):
    qube.mailcap_hardened()


def test_sd_client_package_installed(qube):
    assert qube.package_is_installed("securedrop-client")


def test_sd_client_dependencies_installed(qube):
    assert qube.package_is_installed("python3-pyqt5")
    assert qube.package_is_installed("python3-pyqt5.qtsvg")


def test_sd_client_config(dom0_config, qube):
    assert dom0_config["submission_key_fpr"] == qube.vm_config_read("SD_SUBMISSION_KEY_FPR")


def test_logging_configured(qube):
    qube.logging_configured()
