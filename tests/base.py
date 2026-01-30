"""
Generalized helper functions for testing the SecureDrop Workstation setup.
Aims to provide a DRY configuration for the pytest suite.
"""

import json
import os
import re
import subprocess

import dnf
import pytest
from qubesadmin import Qubes

# Reusable constant for DRY import across tests
DEBIAN_VERSION = "bookworm"
SD_TEMPLATE_BASE = f"sd-base-{DEBIAN_VERSION}-template"
SD_TEMPLATE_LARGE = f"sd-large-{DEBIAN_VERSION}-template"
SD_TEMPLATE_SMALL = f"sd-small-{DEBIAN_VERSION}-template"

SD_TAG = "sd-workstation"  # Tag identifying SecureDrop Workstation-managed VMs

# Expectations regarding VMs' existence and versions
SD_VMS = ["sd-gpg", "sd-log", "sd-proxy", "sd-app", "sd-viewer", "sd-devices"]
SD_DVM_TEMPLATES = ["sd-devices-dvm", "sd-proxy-dvm"]
SD_TEMPLATES = [SD_TEMPLATE_BASE, SD_TEMPLATE_LARGE, SD_TEMPLATE_SMALL]
SD_UNTAGGED_DEPRECATED_VMS = ["sd-retain-logvm"]

CURRENT_FEDORA_VERSION = "42"
CURRENT_FEDORA_TEMPLATE = "fedora-" + CURRENT_FEDORA_VERSION + "-xfce"
CURRENT_FEDORA_DVM = "fedora-" + CURRENT_FEDORA_VERSION + "-dvm"
CURRENT_WHONIX_VERSION = "17"


# Lifted from launcher/sdw_util/Util.py
def get_qubes_version():
    """
    Helper function for checking the Qubes version. Returns None if not on Qubes.
    """
    is_qubes = False
    version = None
    try:
        with open("/etc/os-release") as f:
            for line in f:
                try:
                    key, value = line.rstrip().split("=")
                except ValueError:
                    continue
                if key == "NAME" and "qubes" in value.lower():
                    is_qubes = True
                if key == "VERSION_ID":
                    version = value
    except FileNotFoundError:
        return None
    if not is_qubes:
        return None
    return version


def get_mimeapp_vars_for_vm(vm_name):
    """
    Retrieve test fixture vars for inspecting MIME type handling for this VM.
    Assumes that hardcoded vars file exists on disk, adjacent to the test, named as
    `vars/{vm_name}.mimeapps`.

    We do this via a helper function, rather than via pytest fixtures, in order
    to leverage parametrization for parallel test execution.
    """
    filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "vars", f"{vm_name}.mimeapps"
    )
    with open(filepath) as f:
        lines = f.readlines()
        for line in lines:
            if line != "[Default Applications]\n" and not line.startswith("#"):
                mime_type = line.split("=")[0]
                expected_app = line.split("=")[1].rstrip().rstrip(";")
                yield (mime_type, expected_app)


def is_managed_qube(qube):
    """
    Help assess if qube is to be managed directly

    Currently excluded qubes:
    - preloaded qubes: they are restarted when changes are
    applied to tempaltes and do no need explicit management.
    """
    return not getattr(qube, "is_preload", False)


def is_workstation_qube(qube):
    """
    Is the qube a managed, workstation-tagged qube?

    NOTE: filter out the "sd-viewer-disposable" qube, which is an ephemeral
    DispVM, which will exist at certain points of the test suite
    """

    return is_managed_qube(qube) and SD_TAG in qube.tags and qube.name != "sd-viewer-disposable"


class QubeWrapper:
    def __init__(
        self,
        name,
        expected_config_keys=set(),
        linux_security_modules="apparmor",
        enforced_apparmor_profiles=set(),
        mime_types_handling=False,
        mime_vars_vm_name=None,
        devices_attachable=False,
    ):
        """
        QubesVM test helper.

        Keyword arguments:
            expected_config_keys -- QubesDB's vm-config expected keys
            linux_security_modules -- Linux Security Module (LSM) expected
            enforced_apparmor_profiles -- AppArmor profiles expected
            mime_types_handling -- Whether to run MIME types tests for this VM
            mime_vars_vm_name -- VM name to use for MIME vars file lookup (defaults to name)
            devices_attachable -- VM can have devices attached to it
        """

        self.name = name
        self.app = Qubes()
        self.vm = self.app.domains[self.name]
        if self.vm.is_running():
            pass
        else:
            self.vm.start()

        self.expected_config_keys = expected_config_keys
        self.linux_security_modules = linux_security_modules
        self.enforced_apparmor_profiles = enforced_apparmor_profiles
        self.mime_types_handling = mime_types_handling
        self.mime_vars_vm_name = mime_vars_vm_name if mime_vars_vm_name else name
        self.devices_attachable = devices_attachable

    def run(self, cmd, user=""):
        """
        Wrapper for `Qube.run()` to make it a bit more ergonomic in tests.
        """
        full_cmd = ["qvm-run", "-p"]
        if user:
            full_cmd += ["-u", user]
        full_cmd += [self.name, cmd]
        return subprocess.check_output(full_cmd).decode("utf-8").strip()

    def get_file_contents(self, path):
        cmd = ["qvm-run", "-p", self.name, f"sudo /bin/cat {path}"]
        return subprocess.check_output(cmd).decode("utf-8")

    def get_symlink_location(self, path):
        cmd = ["qvm-run", "-p", self.name, f"/usr/bin/readlink -f {path}"]
        return subprocess.check_output(cmd).decode("utf-8").strip()

    def package_is_installed(self, pkg):
        """
        Confirms that a given package is installed inside the VM.
        """
        # dpkg --verify will exit non-zero for a non-installed pkg,
        # catch that and return False
        try:
            subprocess.check_call(["qvm-run", "-a", "-q", self.name, f"dpkg --verify {pkg}"])
        except subprocess.CalledProcessError:
            return False

        return True

    def service_is_active(self, service):
        try:
            results = self.run(f"sudo systemctl is-active {service}")
        except subprocess.CalledProcessError as e:
            if e.returncode == 3:
                return False  # exit code 3 == inactive
            else:
                raise e
        return results == "active"

    def assertFileHasLine(self, remote_path, wanted_line):
        remote_content = self.get_file_contents(remote_path)
        lines = remote_content.splitlines()
        for line in lines:
            if line == wanted_line:
                return True
        msg = f"File {remote_path} does not contain expected line {wanted_line}"
        raise AssertionError(msg)

    def fileExists(self, remote_path) -> bool:
        # ls will return non-zero if the file doesn't exist
        # and error will be propagated to the test runner,
        # so we catch that case and return false.
        try:
            subprocess.check_call(["qvm-run", "-a", "-q", self.name, f"ls {remote_path}"])
        except subprocess.CalledProcessError:
            return False

        return True

    def qubes_service_enabled(self, service):
        """Check whether the named Qubes service is enabled on this
        VM."""
        return self.fileExists(f"/var/run/qubes-service/{service}")

    def vm_config_read(self, key):
        """Read `key` from the QubesDB `/vm-config/` hierarchy and return its
        value if set, otherwise `None`.
        """
        try:
            return self.run(f"qubesdb-read /vm-config/{key}")
        except subprocess.CalledProcessError:
            return None

    def vm_config_check(self, expected):
        """Check that the set of expected by the VM keys equals the set of keys
        actually configured.
        """
        actual = set(self.run("qubesdb-list /vm-config/").split("\n"))
        actual.discard("")  # if "qubesdb-list" returned nothing
        assert actual == set(expected)

    def logging_configured(self):
        """
        Make sure rsyslog is configured to send in data to sd-log vm.
        """
        # Logging is not disabled
        assert not self.fileExists("/var/run/qubes-service/securedrop-logging-disabled")

        assert self.package_is_installed("securedrop-log")
        assert self.fileExists("/usr/sbin/sd-rsyslog")
        assert self.fileExists("/etc/rsyslog.d/sdlog.conf")
        assert self.fileExists("/etc/sd-rsyslog.conf")
        # Then we check the configuration inside of the file.
        file_content = self.get_file_contents("/etc/sd-rsyslog.conf")
        static_content = """[sd-rsyslog]
remotevm = sd-log
"""
        assert file_content == static_content
        # Check for evidence of misconfigured logging in syslog,
        # fail if matching events found
        # Several VMs show this error message even though they're shipping logs,
        # so let's investigate further.
        # cmd_output = self.run("sudo grep -F \"action 'action-0-omprog' suspended (module 'omprog')\" /var/log/syslog | wc -l").strip()  # noqa
        # assert cmd_output == "0"

    def mailcap_hardened(self):
        """
        Ensure that mailcap rules are not used as a fallback when looking up
        appropriate viewer applications for files of a given MIME type.
        """

        # Ensure that mailcap configuration files are present in the expected
        # locations and contain the expected contents. Rules in `~/.mailcap`
        # take precedence over those in `/etc/mailcap`.
        assert self.fileExists("/home/user/.mailcap")
        assert self.fileExists("/opt/sdw/mailcap.default")
        self.assertFileHasLine("/home/user/.mailcap", '*/*; logger "Mailcap is disabled."')

        # Because we target an AppVM, we cannot easily use the Pyhton tempfile
        # module here without relying on a helper script. Instead, we use the
        # mktemp utility to create a test file with the OpenDocument extension.
        tmpfile_name = self.run("mktemp -t XXXXXX.odt")

        # The --norun argument ensures that we do not launch any application,
        # regardless of the result of this invocation.
        mailcap_result = self.run(f"run-mailcap --norun {tmpfile_name}")

        # For simplicity, we remove the tempfile here instead of in a separate
        # teardown method.
        self.run(f"rm {tmpfile_name}")

        # Ensure that the wildcard rule worked as expected.
        assert mailcap_result == f'logger "Mailcap is disabled." <{tmpfile_name}'


class Test_SD_VM_Common:
    def test_vm_config_keys(self, qube):
        """Every VM should check that it has only the configuration keys it
        expects.
        """
        qube.vm_config_check(qube.expected_config_keys)

    def test_lsm_enabled(self, qube):
        """Check that the expected LSM is enabled"""
        if qube.linux_security_modules == "apparmor":
            assert qube.package_is_installed("apparmor")
            # returns error code if AppArmor not enabled
            qube.run("sudo aa-status --enabled")
        elif qube.linux_security_modules == "selinux":
            sestatus = qube.run("sudo sestatus")
            assert "SELinux status:                 enabled\n" in sestatus
            assert "Current mode:                   enforcing\n" in sestatus
        else:
            raise ValueError(f"Unsupported LSM: {qube.linux_security_modules}")

    def test_enforced_apparmor_profiles(self, qube):
        """Check the expected AppArmor profiles are enforced"""
        if not qube.enforced_apparmor_profiles:
            pytest.skip(f"No enforced AppArmor profiles in {qube.name}")

        results = json.loads(qube.run("sudo aa-status --json"))
        for profile in qube.enforced_apparmor_profiles:
            assert results["profiles"][profile] == "enforce"

    def test_grsec_kernel(self, qube):
        """
        Confirms expected grsecurity-patched kernel is running.
        """
        # base doesn't have kernel configured
        exceptions = [SD_TEMPLATE_BASE, "sys-usb"]

        if qube.vm.name in exceptions:
            pytest.skip(f"Skipping grsec test on VM: '{qube.vm.name}'")

        # Running custom kernel in PVH mode requires pvgrub2-pvh
        assert qube.vm.virt_mode == "pvh"
        assert qube.vm.kernel == "pvgrub2-pvh"

        # Check running kernel is grsecurity-patched
        stdout = qube.run("uname -r")
        assert stdout.endswith("-grsec-workstation")
        qube.service_is_active("paxctld")

    def test_debian_platform_version(self, qube):
        """
        Asserts that the given AppVM is based on an OS listed in the
        SUPPORTED_<XX>_PLATFORMS list, as specified in tests.
        All workstation-provisioned VMs should be based on DEBIAN_VERSION.
        """

        if qube.name.startswith("sys-"):
            pytest.skip(f"skipping Debian platform check on QubesOS sys VM: {qube.name}")

        stdout = qube.run("cat /etc/os-release")
        search = re.search(r'^PRETTY_NAME="(.*)"', stdout)
        if not search:
            raise RuntimeError(f"Unable to determine platform for {qube.name}")
        platform = search.group(1)
        assert DEBIAN_VERSION in platform

    @pytest.mark.mime
    @pytest.mark.slow
    @pytest.mark.configuration
    def test_mime_types(self, qube):
        """
        Functionally verifies that the VM config handles specific filetypes correctly,
        opening them with the appropriate program.
        """
        if not qube.mime_types_handling:
            pytest.skip(f"MIME types handling not enabled for {qube.name}")

        for mime_type, expected_app in get_mimeapp_vars_for_vm(qube.mime_vars_vm_name):
            actual_app = qube.run(f"xdg-mime query default {mime_type}")
            assert (
                actual_app == expected_app
            ), f"MIME type {mime_type}: expected {expected_app}, got {actual_app}"

    @pytest.mark.skipif(
        dnf.rpm.detect_releasever("/") == "4.2", reason="Feature only available in Qubes >= 4.3"
    )
    def test_mock_device_attach_deny(self, qube, mock_block_device, qubesd_log):
        if qube.name == "sys-usb":
            pytest.skip("Test does not run on 'sys-usb' (no need to attach devices to itself)")
        if qube.devices_attachable:
            pytest.skip("On this qube device attachment is not denied")

        # Device attachment expected to fail (generic qubes)
        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            subprocess.check_output(
                ["qvm-block", "attach", qube.name, mock_block_device],
                stderr=subprocess.STDOUT,  # Capture qubesd error message
                text=True,
            )

        assert "Error: Got empty response from qubesd" in exc_info.value.stdout

        # Previous error too generic: Dig into journal logs to confirm attachment denial
        expected_re = re.compile(
            (
                r"WARNING: permission denied for call "
                r"b'admin.vm.device.block.Attach'\+b'{device_id}\+\+\d+' "
                r"\(b'dom0' → b'{target_qube}'\)"
            ).format(device_id=mock_block_device.replace(":", r"\+"), target_qube=qube.name)
        )

        # Exactly one policy denial match
        matching_entries = list(filter(expected_re.match, qubesd_log))
        assert len(matching_entries) == 1
