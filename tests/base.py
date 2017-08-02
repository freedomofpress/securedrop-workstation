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

class SD_VM_Tests(unittest.TestCase):
  def setUp(self):
    self.qc = QubesVmCollection()
    self.qc.lock_db_for_reading()
    self.qc.load()

  def tearDown(self):
    self.qc.unlock_db()

  def test_expected(self):
    vms = [v.name for v in self.qc.values()]
    vm_set = set(vms)

    for test_vm in ["sd-whonix", "sd-journalist", "sd-svs", "sd-gpg", "fedora-23-sd-dispvm"]:
      self.assertTrue(test_vm in vm_set)

  def test_sd_whonix_net(self):
    vm = self.qc.get_vm_by_name("sd-whonix")
    nvm = vm.netvm
    self.assertTrue(nvm.name == "sys-firewall")

  def test_sd_journalist_net(self):
    vm = self.qc.get_vm_by_name("sd-journalist")
    nvm = vm.netvm
    self.assertTrue(nvm.name == "sd-whonix")

  def test_sd_svs_net(self):
    vm = self.qc.get_vm_by_name("sd-svs")
    nvm = vm.netvm
    self.assertTrue(nvm is None)

  def test_sd_gpg_net(self):
    vm = self.qc.get_vm_by_name("sd-gpg")
    nvm = vm.netvm
    self.assertTrue(nvm is None)

  def test_sd_dispvm_net(self):
    vm = self.qc.get_vm_by_name("fedora-23-sd-dispvm")
    nvm = vm.netvm
    self.assertTrue(nvm.name == "sys-firewall")


class SD_VM_Local_Test(unittest.TestCase):

  def setUp(self):
    self.qc = QubesVmCollection()
    self.qc.lock_db_for_reading()
    self.qc.load()
    self.vm = self.qc.get_vm_by_name(self.vm_name)
    #self._reboot()

  def tearDown(self):
    #self.vm.shutdown()
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

#suite = unittest.TestLoader().loadTestsFromTestCase(SD_VM_Tests)
#unittest.TextTestRunner(verbosity=2).run(suite)
