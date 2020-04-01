import unittest
import time

from reboot_sdw_vms import shutdown_and_start_vms


TRY_COUNT = 10

class SD_Reboot_Tests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_shutdown_and_start_vms_naively(self):
        """
        Naively perform the reboot-all loop several times.
        """
        failure_count = 0
        for i in range(TRY_COUNT):
            try:
                shutdown_and_start_vms()
            except:
                failure_count += 1
                pass
            time.sleep(1)

        assert failure_count == 0
