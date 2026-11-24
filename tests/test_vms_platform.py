import os
import subprocess
from datetime import datetime, timedelta

import pytest
from qubesadmin.app import VMCollection
from qubesadmin.vm import QubesVM

from tests.base import (
    CURRENT_FEDORA_TEMPLATE,
    DEBIAN_CODENAME,
    SD_ADMIN_TEMPLATE,
    SD_INBOX_TEMPLATE,
    SD_VIEWER_TEMPLATE,
)
from tests.markers import needs_journalist

IS_CI = os.environ.get("CI") == "true"


def _check_packages_up_to_date(vm: QubesVM, fedora: bool = False) -> bool:
    """
    Checks that all available package updates are installed;
    no upgrades pending. Assumes VM is Debian-based, so uses apt,
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
@pytest.mark.parametrize(
    ("vm_name", "needs"),
    [
        (SD_INBOX_TEMPLATE, "needs_journalist"),
        (SD_VIEWER_TEMPLATE, "needs_journalist"),
        (SD_ADMIN_TEMPLATE, "needs_admin"),
    ],
)
@pytest.mark.skipif(IS_CI, reason="Skipping on CI")
def test_all_sd_templates_uptodate(
    vm_name: str, needs: str, request: pytest.FixtureRequest, all_vms: VMCollection
) -> None:
    """
    Asserts that all VMs have all available apt packages at the latest
    versions, with no updates pending.
    """
    request.getfixturevalue(needs)
    vm = all_vms[vm_name]
    assert _check_packages_up_to_date(vm), f"Unapplied updates for VM '{vm}'"


@pytest.mark.skipif(IS_CI, reason="Skipping on CI")
@pytest.mark.packages
@pytest.mark.configuration
def test_all_fedora_vms_uptodate(all_vms: VMCollection) -> None:
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


@pytest.mark.packages
@pytest.mark.provisioning
def test_qubes_vm_update_ran_on_fedora_template(all_vms: VMCollection) -> None:
    """
    Asserts that the Fedora template used by the workstation has been updated
    at least once after installation.

    Admins are instructed to have they system fully up to date before installing
    the workstation, but we don't expect them to template upgrade, in case the
    Fedora version installed is EOL. Therefore, this checks if the installation
    logic does update the template at least once.
    """
    fedora_template = all_vms[CURRENT_FEDORA_TEMPLATE]

    # When qubes-vm-update runs, it sets the 'last-update' qubes feature
    # to the date
    updated_once = fedora_template.features.get("last-update") not in [None, ""]
    updates_checked = fedora_template.features.get("last-updates-check") not in [None, ""]

    assert (
        updates_checked
    ), f"Updates for '{CURRENT_FEDORA_TEMPLATE}' should have been checked at least once"
    assert updated_once, (
        f"Updates for '{CURRENT_FEDORA_TEMPLATE}' should been done least once.\n"
        "NOTE: there may also be the unlikely scenario where the template is so"
        "fresh that there are no updates. This will be very rare."
    )


@pytest.mark.provisioning
@pytest.mark.parametrize(
    ("vm_name", "needs"),
    [
        (CURRENT_FEDORA_TEMPLATE, "needs_dom0"),
        (SD_VIEWER_TEMPLATE, "needs_journalist"),
        (SD_INBOX_TEMPLATE, "needs_journalist"),
        (SD_ADMIN_TEMPLATE, "needs_admin"),
    ],
)
def test_os_eol(
    vm_name: str, needs: str, request: pytest.FixtureRequest, all_vms: VMCollection
) -> None:
    """
    Ensures the VM's OS is not approaching end-of-life.
    The os-eol qvm feature should contain a date in YYYY-MM-DD format.
    """
    request.getfixturevalue(needs)
    # number of days prior to EOL date that constitutes a test failure
    OS_EOL_BUFFER_DAYS = 30
    qube = all_vms[vm_name]
    eol_str = qube.features.get("os-eol")
    if eol_str is None:
        pytest.skip(f"No os-eol feature set for {qube.name}")

    # Parse the date string
    try:
        eol_date = datetime.strptime(eol_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise AssertionError(f"Invalid os-eol date format '{eol_str}': {e}")

    # Ensure current date is before EOL minus buffer
    today = datetime.now().date()
    buffer_date = eol_date - timedelta(days=OS_EOL_BUFFER_DAYS)

    assert today < buffer_date, (
        f"OS end-of-life approaching for {qube.name}: "
        f"EOL is {eol_date}, within {OS_EOL_BUFFER_DAYS} day buffer"
    )


@needs_journalist
@pytest.mark.provisioning
def test_dispvm_default_platform() -> None:
    """
    Query dom0 Qubes preferences and confirm that new DispVMs
    will be created under a supported OS. Requires a separate
    test because DispVMs may not be running at present.
    """
    cmd = ["qubes-prefs", "default_dispvm"]
    result = subprocess.check_output(cmd).decode("utf-8").rstrip("\n")
    assert result == "sd-viewer"


@pytest.mark.parametrize(
    ("vm_name", "needs"),
    [
        (SD_INBOX_TEMPLATE, "needs_journalist"),
        (SD_VIEWER_TEMPLATE, "needs_journalist"),
        (SD_ADMIN_TEMPLATE, "needs_admin"),
    ],
)
@pytest.mark.configuration
@pytest.mark.packages
def test_sd_vm_apt_sources(
    vm_name: str,
    needs: str,
    request: pytest.FixtureRequest,
    dom0_config_environment: str,
    all_vms: VMCollection,
) -> None:
    """
    Test that the three templates we install our apt sources into are correct
    """
    request.getfixturevalue(needs)
    vm = all_vms[vm_name]

    # First, check the prod apt repo is configured, which happens unconditionally
    # via securedrop-keyring deb package
    assert_apt_source(
        vm,
        "main",
        "https://apt.freedom.press",
        "/etc/apt/sources.list.d/apt_freedom_press.sources",
    )

    if dom0_config_environment == "prod":
        # No test sources should be present
        stdout, stderr = vm.run("ls /etc/apt/sources.list.d/")
        sources_list = stdout.decode("utf-8").rstrip("\n")
        assert "apt-test_freedom_press.sources" not in sources_list
        return

    # we're in staging or dev, so check for that file
    components = ["main"]
    if dom0_config_environment == "dev":
        components.append("nightlies")

    assert_apt_source(
        vm,
        " ".join(components),
        "https://apt-test.freedom.press",
        "/etc/apt/sources.list.d/apt-test_freedom_press.sources",
    )


@pytest.mark.configuration
@pytest.mark.packages
def assert_apt_source(vm: QubesVM, component: str, url: str, filename: str) -> None:
    stdout, stderr = vm.run(f"cat {filename}")
    contents = stdout.decode("utf-8").rstrip("\n")

    assert f"Components: {component}\n" in contents, f"{vm.name} wrong component"
    assert f"URIs: {url}\n" in contents, f"{vm.name} wrong URL"
    assert f"Suites: {DEBIAN_CODENAME}\n" in contents, f"{vm.name} wrong suite/codename"
