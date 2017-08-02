import unittest

def load_tests(loader, tests, pattern):
  tests = unittest.TestSuite()

  for modname in (
      'tests.vms-exist',
      'tests.svs-test'
      ):
    tests.addTest(loader.loadTestsFromName(modname))

  return tests

