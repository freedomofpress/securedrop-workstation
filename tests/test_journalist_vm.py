from distutils import spawn

import os
import re
import subprocess
import time
import unittest

import qubes.tests
import qubes.qubes

from qubes.qubes import QubesVmCollection

from base import SD_VM_Local_Test

class SD_Journalist_Tests(SD_VM_Local_Test):
  def setUp(self):
    self.vm_name = "sd-journalist"
    super(SD_Journalist_Tests, self).setUp()

  def test_accept_sd_xfer_extracted_file(self):
    self.assertFilesMatch(
     "/usr/local/bin/move-to-svs",
     "sd-journalist/move-to-svs")

def load_tests(loader, tests, pattern):
  suite = unittest.TestLoader().loadTestsFromTestCase(SD_Journalist_Tests)
  return suite
