import os
import unittest

from base import SD_Unnamed_DVM_Local_Test


class SD_Viewer_Tests(SD_Unnamed_DVM_Local_Test):
    @classmethod
    def setUpClass(cls):
        super().setUpClass("sd-viewer")

    def setUp(self):
        super().setUp()
        self.expected_config_keys = {"SD_MIME_HANDLING"}
        # this is not a comprehensive list, just a few that users are likely to use
        self.enforced_apparmor_profiles = {
            "/usr/bin/evince",
            "/usr/bin/evince-previewer",
            "/usr/bin/evince-previewer//sanitized_helper",
            "/usr/bin/evince-thumbnailer",
            "/usr/bin/totem",
            "/usr/bin/totem-audio-preview",
            "/usr/bin/totem-video-thumbnailer",
            "/usr/bin/totem//sanitized_helper",
        }

    def test_sd_viewer_metapackage_installed(self):
        self.assertTrue(self._package_is_installed("securedrop-workstation-viewer"))
        self.assertFalse(self._package_is_installed("securedrop-workstation-svs-disp"))

    def test_sd_viewer_evince_installed(self):
        pkg = "evince"
        self.assertTrue(self._package_is_installed(pkg))

    def test_sd_viewer_libreoffice_installed(self):
        self.assertTrue(self._package_is_installed("libreoffice"))

    def test_logging_configured(self):
        self.logging_configured()

    def test_redis_packages_not_installed(self):
        """
        Only the log collector, i.e. sd-log, needs redis, so redis will be
        present in small template, but not in large.
        """
        self.assertFalse(self._package_is_installed("redis"))
        self.assertFalse(self._package_is_installed("redis-server"))

    def test_mime_types(self):
        filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "vars", "sd-viewer.mimeapps"
        )
        with open(filepath) as f:
            lines = f.readlines()
            for line in lines:
                if line != "[Default Applications]\n" and not line.startswith("#"):
                    mime_type = line.split("=")[0]
                    expected_app = line.split("=")[1].rstrip()
                    actual_app = self._run(f"xdg-mime query default {mime_type}")
                    self.assertEqual(actual_app, expected_app)

    def test_mimetypes_service(self):
        self._service_is_active("securedrop-mime-handling")

    def test_mailcap_hardened(self):
        self.mailcap_hardened()

    def test_mimetypes_symlink(self):
        self.assertTrue(self._fileExists(".local/share/applications/mimeapps.list"))
        symlink_location = self._get_symlink_location(".local/share/applications/mimeapps.list")
        assert symlink_location == "/opt/sdw/mimeapps.list.sd-viewer"


def load_tests(loader, tests, pattern):
    return unittest.TestLoader().loadTestsFromTestCase(SD_Viewer_Tests)
