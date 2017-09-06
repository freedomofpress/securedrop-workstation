import unittest

def load_tests(loader, tests, pattern):
  tests = unittest.TestSuite()

  for modname in (
      'tests.vms_exist',
      'tests.svs_test',
      'tests.test_journalist_vm',
      'tests.test_sd_whonix',
      'tests.test_dispvm',
      'tests.test_sd_gpg'
      ):
    tests.addTest(loader.loadTestsFromName(modname))

  return tests
