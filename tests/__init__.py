import unittest

def load_tests(loader, tests, pattern):
  print "tests {}".format(tests)
  suite = unittest.TestSuite()
  suite.addTests(tests)
  print "suite {}".format(suite)
  for modname in (
      'tests.vms_exist',
      'tests.svs_test',
      'tests.test_journalist_vm',
      'tests.test_sd_whonix',
      'tests.test_dispvm'
      ):
    suite.addTest(loader.loadTestsFromName(modname))
  print "suite {}".format(suite)
  return suite
