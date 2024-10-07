import unittest

from base import SD_VM_Local_Test


class SD_App_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-app"
        super().setUp()
        self.expected_config_keys = {
            "QUBES_GPG_DOMAIN",
            "SD_SUBMISSION_KEY_FPR",
            "SD_MIME_HANDLING",
        }
        self.enforced_apparmor_profiles = {"/usr/bin/securedrop-client"}

    def test_open_in_dvm_desktop(self):
        contents = self._get_file_contents("/usr/share/applications/open-in-dvm.desktop")
        expected_contents = [
            "TryExec=/usr/bin/qvm-open-in-vm",
            "Exec=/usr/bin/qvm-open-in-vm --view-only @dispvm:sd-viewer %f",
        ]
        for line in expected_contents:
            self.assertIn(line, contents)

    def test_mimeapps(self):
        results = self._run("cat /usr/share/applications/mimeapps.list")
        for line in results.splitlines():
            if line.startswith(("#", "[Default")):
                # Skip comments and the leading [Default Applications]
                continue
            mime, target = line.split("=", 1)
            self.assertEqual(target, "open-in-dvm.desktop;")
            # Now functionally test it
            actual_app = self._run(f"xdg-mime query default {mime}")
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

    def test_logging_configured(self):
        self.logging_configured()


def load_tests(loader, tests, pattern):
    return unittest.TestLoader().loadTestsFromTestCase(SD_App_Tests)
