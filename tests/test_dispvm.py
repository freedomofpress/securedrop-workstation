from distutils import spawn

import os
import re
import subprocess
import time
import unittest

import qubes.tests
import qubes.qubes

from qubes.qubes import QubesVmCollection

# We want to start a dispvm, then assert various files are there.

class Dispvm_Tests(unittest.TestCase):
  def _get_file_contents(self, path):
    p = subprocess.Popen(["/usr/lib/qubes/qfile-daemon-dvm",
                                 "qubes.VMShell",
                                 "dom0",
                                 "DEFAULT"],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=open(os.devnull, 'w'),
                                universal_newlines=True)

    (res, err) = p.communicate("cat {}".format(path))
    self.assertEquals(p.returncode, 0)
    return res

  def assertFilesMatch(self, remote_path, local_path):
    remote_content = self._get_file_contents(remote_path)
    content = False
    with open(local_path) as f:
      content = f.read()
    self.assertTrue(remote_content == content)

  def test_decrypt_sd_submission(self):
    self.assertFilesMatch(
      "/usr/bin/decrypt-sd-submission",
      "decrypt/decrypt-sd-submission"
    )

  def test_application_x_sd_xfer(self):
    self.assertFilesMatch(
      "/usr/share/mime/packages/application-x-sd-xfer.xml",
      "decrypt/application-x-sd-xfer.xml"
    )

  def test_decrypt_sd_submission_desktop(self):
    self.assertFilesMatch(
      "/usr/share/applications/decrypt-sd-submission.desktop",
      "decrypt/decrypt-sd-submission.desktop"
    )

  # we'll need to run gpg --list-secret-keys or whatever and
  # assert that our key is in the keyring
  # def test_sd_journalist_key(self):
  #   self.assertFilesMatch(
  #     "/tmp/sd-journalist.sec",
  #     "sd-journalist.sec"
  #   )



def load_tests(loader, tests, pattern):
  suite = unittest.TestLoader().loadTestsFromTestCase(Dispvm_Tests)
  return suite
