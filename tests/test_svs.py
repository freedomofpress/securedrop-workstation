from distutils import spawn

import os
import re
import subprocess
import time
import unittest

#import qubes.tests
#import qubes.qubes

from qubes.qubes import QubesVmCollection

from base import SD_VM_Local_Test

class SD_SVS_Tests(SD_VM_Local_Test):
  def setUp(self):
    self.vm_name = "sd-svs"
    super(SD_SVS_Tests, self).setUp()

  def test_accept_sd_xfer_extracted_file(self):
    self.assertFilesMatch(
     "/usr/local/bin/accept-sd-xfer-extracted",
     "sd-svs/accept-sd-xfer-extracted")

  def test_xfer_extracted_mime_type(self):
    self.assertFilesMatch(
      "/usr/local/share/mime/packages/application-x-sd-xfer-extracted.xml",
      "sd-svs/application-x-sd-xfer-extracted.xml")

  def test_xfer_extracted_desktop(self):
    self.assertFilesMatch(
      "/usr/local/share/applications/accept-sd-xfer-extracted.desktop",
      "sd-svs/accept-sd-xfer-extracted.desktop")

  def test_open_in_dvm_desktop(self):
    self.assertFilesMatch(
      "/usr/local/share/applications/open-in-dvm.desktop",
      "sd-svs/open-in-dvm.desktop")

  def test_mimeapps(self):
    self.assertFilesMatch(
      "/home/user/.config/mimeapps.list",
      "sd-svs/mimeapps.list")

def load_tests(loader, tests, pattern):
  suite = unittest.TestLoader().loadTestsFromTestCase(SD_SVS_Tests)
  return suite
