import unittest

from base import SD_VM_Local_Test


class SD_Journalist_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-journalist"
        super(SD_Journalist_Tests, self).setUp()

    def test_move_to_svs(self):
        self.assertFilesMatch("/usr/local/bin/move-to-svs",
                              "sd-journalist/move-to-svs")

    def test_sd_process_download(self):
        self.assertFilesMatch("/usr/local/bin/sd-process-download",
                              "sd-journalist/sd-process-download")

    def test_do_not_open_here(self):
        self.assertFilesMatch("/usr/local/bin/do-not-open-here",
                              "sd-journalist/do-not-open-here")

    def test_sd_process_feedback(self):
        self.assertFilesMatch("/usr/local/bin/sd-process-feedback",
                              "sd-journalist/sd-process-feedback")

    def test_sd_process_display(self):
        self.assertFilesMatch("/usr/local/bin/sd-process-display",
                              "sd-journalist/sd-process-display")

    def test_pyqt_installed(self):
        """
        The python-qt4 package is required to populate the PyQt libs
        in the system Python packages. Rather than check for presence
        of the apt package, let's confirm we can actually import the library
        as it's used in the journalist feedback code.
        """
        cmd = "python -c 'import PyQt4.QtCore as QtCore'"
        stdout, stderr = self.vm.run(cmd)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Journalist_Tests)
    return suite
