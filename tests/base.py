from distutils import spawn

import os
import re
import subprocess
import time
import unittest

import qubes.tests
import qubes.qubes

from qubes.qubes import QubesVmCollection

# base class for per-VM testing

class SD_VM_Local_Test(unittest.TestCase):

  def setUp(self):
    self.qc = QubesVmCollection()
    self.qc.lock_db_for_reading()
    self.qc.load()
    self.vm = self.qc.get_vm_by_name(self.vm_name)
    self._reboot()

  def tearDown(self):
    self.vm.shutdown()
    self.qc.unlock_db()

  def _reboot(self):
    if self.vm.is_running():
      self.vm.shutdown()

    while self.vm.is_running():
      time.sleep(1)

    self.vm.start()

  def _get_file_contents(self, path):
    p = self.vm.run("cat {}".format(path), passio_popen=True)
    if p.wait() != 0:
      return None
    return p.stdout.read()

  def assertFilesMatch(self, remote_path, local_path):
    remote_content = self._get_file_contents(remote_path)
    content = False
    with open(local_path) as f:
      content = f.read()
    self.assertTrue(remote_content == content)
