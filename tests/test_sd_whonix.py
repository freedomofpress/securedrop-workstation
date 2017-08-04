from distutils import spawn

import os
import re
import subprocess
import time
import unittest

import qubes.tests
import qubes.qubes

import json
from jinja2 import Template

from qubes.qubes import QubesVmCollection

from base import SD_VM_Local_Test

class SD_Whonix_Tests(SD_VM_Local_Test):
  def setUp(self):
    self.vm_name = "sd-whonix"
    super(SD_Whonix_Tests, self).setUp()

  def test_accept_sd_xfer_extracted_file(self):
    with open("config.json") as c:
      config = json.load(c)
      t = Template("HidServAuth {{ d.hidserv.hostname }} {{ d.hidserv.key }}")
      line = t.render(d=config)
      print line
      self.assertFileHasLine(
        "/etc/tor/torrc",
        line)

def load_tests(loader, tests, pattern):
  suite = unittest.TestLoader().loadTestsFromTestCase(SD_Whonix_Tests)
  return suite
