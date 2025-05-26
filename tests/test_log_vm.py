import secrets
import string
import subprocess

from tests.base import CURRENT_DEBIAN_VERSION, SD_VM_Local_Test


class SD_Log_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-log"
        super().setUp()

    def test_sd_log_package_installed(self):
        assert self._package_is_installed("securedrop-log")

    def test_sd_log_redis_is_installed(self):
        assert self._package_is_installed("redis")
        assert self._package_is_installed("redis-server")

    def test_log_utility_installed(self):
        assert self._fileExists("/usr/sbin/securedrop-log-saver")
        assert self._fileExists("/etc/qubes-rpc/securedrop.Log")

    def test_sd_log_has_no_custom_rsyslog(self):
        assert not self._fileExists("/etc/rsyslog.d/sdlog.conf")

    def test_sd_log_service_running(self):
        assert self._service_is_active("securedrop-log-server")

    def test_redis_service_running(self):
        assert self._service_is_active("redis")

    def test_logs_are_flowing(self):
        """
        To test that logs work, we run a unique command in each VM we care
        about that gets logged, and then check for that string in the logs.
        """
        # Random string, to avoid collisions with other test runs
        token = "".join(secrets.choice(string.ascii_uppercase) for _ in range(10))

        # All @tag:sd-workstation VMs
        all_vms = [vm.name for vm in self.app.domains if "sd-workstation" in vm.tags]
        # base template doesn't have sd-log configured
        # TODO: test a sd-viewer based dispVM
        skip = [f"sd-base-{CURRENT_DEBIAN_VERSION}-template", "sd-viewer"]
        # VMs we expect logs will not go to
        no_log_vms = ["sd-gpg", "sd-log", "sd-whonix"]

        # We first run the command in each VM, and then do a second loop to
        # look for the token in the log entry, so there's enough time for the
        # log entry to get written.
        for vm_name in all_vms:
            if vm_name in skip:
                continue
            # The sudo call will make it into syslog
            subprocess.check_call(["qvm-run", vm_name, f"sudo echo {token}"])

        for vm_name in all_vms:
            if vm_name in skip:
                continue
            syslog = f"/home/user/QubesIncomingLogs/{vm_name}/syslog.log"
            if vm_name in no_log_vms:
                assert not self._fileExists(syslog)
            else:
                assert token in self._get_file_contents(syslog)

    def test_log_dirs_properly_named(self):
        cmd_output = self._run("ls -1 /home/user/QubesIncomingLogs")
        log_dirs = cmd_output.split("\n")
        # Confirm we don't have 'host' entries from Whonix VMs
        assert "host" not in log_dirs
