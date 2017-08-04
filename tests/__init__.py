import unittest

def load_tests(loader, tests, pattern):
  tests = unittest.TestSuite()

  for modname in (
      'tests.vms_exist',
      'tests.svs_test',
      'tests.test_journalist_vm'
      ):
    tests.addTest(loader.loadTestsFromName(modname))

  return tests
