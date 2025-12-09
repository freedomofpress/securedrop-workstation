import os
import subprocess

import pytest

from tests.base import (
    CURRENT_FEDORA_TEMPLATE,
    DEBIAN_VERSION,
    SD_TEMPLATE_LARGE,
    SD_TEMPLATE_SMALL,
    SD_VMS,
)

IS_CI = os.environ.get("CI") == "true"


def _check_packages_up_to_date(vm, fedora=False) -> bool:
    """
    Checks that all available package updates are installed;
    so upgrades pending. Assumes VM is Debian-based, so uses apt,
    but supports `fedora=True` to use dnf instead.

    Returns a boolean so that the calling test can before assertions,
    and report errors with context.
    """
    if not fedora:
        cmd = "apt list --upgradable"
        try:
            stdout, stderr = vm.run(cmd)
            results = stdout.rstrip().decode("utf-8")
            # `apt list` will always print "Listing..." to stdout,
            # so expect only that string.
            return results == "Listing..."
        # apt query should always return 0, so anything else is an error
        except subprocess.CalledProcessError:
            fail_msg = f"failed to check apt updates on VM: {vm}"
            pytest.fail(fail_msg)
    else:
        cmd = "sudo dnf check-update"
        # Will raise CalledProcessError if updates available
        try:
            stdout, stderr = vm.run(cmd)
        except subprocess.CalledProcessError:
            return False
        # 'stdout' will contain timestamped progress info; ignore it, and inspect stderr.
        results = stderr.decode("utf-8")
        stderr_lines = results.split("\n")

        # filter out gpgcheck warning present on all dnf operations
        omit_lines = [
            # ~F41 emitted warnings about GPG signature checks
            "Warning: Enforcing GPG signature check",
            # At least as recently as F42, repo loading messages were visible.
            "Updating and loading repositories:",
            "Repositories loaded.",
        ]
        stderr_lines = [x for x in stderr_lines if x not in omit_lines]

        results = "".join(stderr_lines)
        return results == ""


@pytest.mark.configuration
@pytest.mark.packages
@pytest.mark.parametrize("vm_name", SD_VMS)
@pytest.mark.skipif(IS_CI, reason="Skipping on CI")
def test_all_sd_vms_uptodate(vm_name, all_vms):
    """
    Asserts that all VMs have all available apt packages at the latest
    versions, with no updates pending.
    """
    vm = all_vms[vm_name]
    # We can't perform a live update check via package manager without a NetVM,
    # e.g. for `sd-viewer`
    if not vm.netvm and vm.klass != "TemplateVM":
        pytest.skip(f"skipping package freshness check on net-less VM: '{vm.name}'")

    # Create custom error message, so failing test cases display
    # which VM caused the looped check to fail.
    fail_msg = f"Unapplied updates for VM '{vm}'"
    assert _check_packages_up_to_date(vm), fail_msg


@pytest.mark.skipif(IS_CI, reason="Skipping on CI")
@pytest.mark.packages
@pytest.mark.configuration
def test_all_fedora_vms_uptodate(all_vms):
    """
    Asserts that all Fedora-based templates, such as sys-net, have all
    available packages at the latest versions, with no updates pending.
    """
    # Technically we want to know whether the sys-firewall, sys-net, and
    # sys-usb VMs have their updates installed. This test assumes those
    # AppVMs are based on the most recent Fedora version.
    vm_name = CURRENT_FEDORA_TEMPLATE
    vm = all_vms[vm_name]
    fail_msg = f"Unapplied updates for VM '{vm}'"
    assert _check_packages_up_to_date(vm, fedora=True), fail_msg
    vm.shutdown()


@pytest.mark.provisioning
def test_dispvm_default_platform():
    """
    Query dom0 Qubes preferences and confirm that new DispVMs
    will be created under a supported OS. Requires a separate
    test because DispVMs may not be running at present.
    """
    cmd = ["qubes-prefs", "default_dispvm"]
    result = subprocess.check_output(cmd).decode("utf-8").rstrip("\n")
    assert result == "sd-viewer"


@pytest.mark.configuration
@pytest.mark.packages
def test_sd_vm_apt_sources(config, all_vms):
    """
    Test that the three templates we install our apt sources into are correct
    """
    for vm_name in [
        SD_TEMPLATE_SMALL,
        SD_TEMPLATE_LARGE,
    ]:
        vm = all_vms[vm_name]

        # First, check the prod apt repo is configured, which happens unconditionally
        # via securedrop-keyring deb package
        assert_apt_source(
            vm,
            "main",
            "https://apt.freedom.press",
            "/etc/apt/sources.list.d/apt_freedom_press.sources",
        )

        if config["environment"] == "prod":
            # No test sources should be present
            stdout, stderr = vm.run("ls /etc/apt/sources.list.d/")
            sources_list = stdout.decode("utf-8").rstrip("\n")
            assert "apt-test_freedom_press.sources" not in sources_list
            continue

        # we're in staging or dev, so check for that file
        components = ["main"]
        if config["environment"] == "dev":
            components.append("nightlies")

        assert_apt_source(
            vm,
            " ".join(components),
            "https://apt-test.freedom.press",
            "/etc/apt/sources.list.d/apt-test_freedom_press.sources",
        )


@pytest.mark.configuration
@pytest.mark.packages
def assert_apt_source(vm, component, url, filename):
    stdout, stderr = vm.run(f"cat {filename}")
    contents = stdout.decode("utf-8").rstrip("\n")

    assert f"Components: {component}\n" in contents, f"{vm.name} wrong component"
    assert f"URIs: {url}\n" in contents, f"{vm.name} wrong URL"
    assert f"Suites: {DEBIAN_VERSION}\n" in contents, f"{vm.name} wrong suite/codename"
