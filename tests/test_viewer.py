import os

from base import SD_VM_Local_Test


class SD_Viewer_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-viewer"
        super(SD_Viewer_Tests, self).setUp()

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
        with open(filepath, "r") as f:
            lines = f.readlines()
            for line in lines:
                if line != "[Default Applications]\n" and not line.startswith("#"):
                    mime_type = line.split("=")[0]
                    expected_app = line.split("=")[1].rstrip()
                    actual_app = self._run("xdg-mime query default {}".format(mime_type))
                    self.assertEqual(actual_app, expected_app)

    def test_mailcap_hardened(self):
        self.mailcap_hardened()

    def test_mimetypes_symlink(self):
        self.assertTrue(self._fileExists(".local/share/applications/mimeapps.list"))
        symlink_location = self._get_symlink_location(".local/share/applications/mimeapps.list")
        assert symlink_location == "/opt/sdw/mimeapps.list.sd-viewer"

    def test_gpg_domain_configured(self):
        self.qubes_gpg_domain_configured(self.vm_name)
