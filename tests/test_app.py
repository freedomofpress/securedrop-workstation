import json
import unittest

from base import SD_VM_Local_Test


class SD_App_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-app"
        super(SD_App_Tests, self).setUp()

    def test_gpg_domain_configured(self):
        self.qubes_gpg_domain_configured(self.vm_name)

    def test_open_in_dvm_desktop(self):
        contents = self._get_file_contents("/usr/share/applications/open-in-dvm.desktop")
        expected_contents = [
            "TryExec=/usr/bin/qvm-open-in-vm",
            "Exec=/usr/bin/qvm-open-in-vm --view-only @dispvm:sd-viewer %f",
        ]
        for line in expected_contents:
            self.assertTrue(line in contents)

    def test_mimeapps(self):
        cmd = "perl -F= -lane 'print $F[1]' /usr/share/applications/mimeapps.list | sort | uniq -c"
        results = self._run(cmd)
        expected_results = "2 \n    295 open-in-dvm.desktop;"
        self.assertEqual(results, expected_results)

    def test_mimeapps_functional(self):
        cmd = "perl -F= -lane 'print $F[0]' /usr/share/applications/mimeapps.list"
        results = self._run(cmd)
        for line in results.split("\n"):
            if line != "[Default Applications]" and not line.startswith("#"):
                actual_app = self._run("xdg-mime query default {}".format(line))
                self.assertEqual(actual_app, "open-in-dvm.desktop")

    def test_mailcap_hardened(self):
        self.mailcap_hardened()

    def test_sd_client_package_installed(self):
        self.assertTrue(self._package_is_installed("securedrop-client"))

    def test_sd_client_dependencies_installed(self):
        self.assertTrue(self._package_is_installed("python3-pyqt5"))
        self.assertTrue(self._package_is_installed("python3-pyqt5.qtsvg"))

    def test_sd_client_config(self):
        self.assertEqual(
            self.dom0_config["submission_key_fpr"], self._vm_config_read("SD_SUBMISSION_KEY_FPR")
        )

    def test_sd_client_apparmor(self):
        cmd = "sudo aa-status --json"
        results = json.loads(self._run(cmd))
        self.assertTrue(results["profiles"]["/usr/bin/securedrop-client"] == "enforce")

    def test_logging_configured(self):
        self.logging_configured()


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_App_Tests)
    return suite
