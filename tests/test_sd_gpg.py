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

class SD_GPG_Tests(SD_VM_Local_Test):
  def setUp(self):
    self.vm_name = "sd-gpg"
    super(SD_GPG_Tests, self).setUp()

  def test_sd_submission_key_is_available(self):
    # See what private keys are available
    gpg_k_output = subprocess.call(['gpg', '-K'])
    self.assertIn("Test SecureDrop Submission Key", gpg_k_output)

def load_tests(loader, tests, pattern):
  suite = unittest.TestLoader().loadTestsFromTestCase(SD_GPG_Tests)
  return suite
