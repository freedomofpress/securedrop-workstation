import os
import subprocess

from unittest import mock
from importlib.machinery import SourceFileLoader
from multiprocessing import Pool
from tempfile import TemporaryDirectory

relpath_notify = "../sdw_notify/Notify.py"
path_to_notify = os.path.join(os.path.dirname(os.path.abspath(__file__)), relpath_notify)
notify = SourceFileLoader("Notify", path_to_notify).load_module()

relpath_updater = "../sdw_updater_gui/Updater.py"
path_to_updater = os.path.join(os.path.dirname(os.path.abspath(__file__)), relpath_updater)
updater = SourceFileLoader("Updater", path_to_updater).load_module()


@mock.patch("Notify.sdlog.error")
@mock.patch("Notify.sdlog.info")
def test_notify_lock(mocked_info, mocked_error):
    """
    Test whether we can successfully obtain an exclusive lock for the notifier
    script
    """
    with TemporaryDirectory() as tmpdir:
        notify.LOCK_FILE_NOTIFIER = os.path.join(tmpdir, "sdw-launcher.lock")
        pid = os.getpid()
        lh = notify.obtain_notify_lock()  # noqa: F841
        # No handled exception should occur
        assert not mocked_error.called
        cmd = ['lsof', '-w', notify.LOCK_FILE_NOTIFIER]
        output_lines = subprocess.check_output(cmd).decode("utf-8").strip().split('\n')
        # We expect exactly one process to be accessing this file, plus output header
        assert len(output_lines) == 2
        lsof_data = output_lines[1].split()
        # We expect the output to have the standard number of fields
        assert len(lsof_data) == 9
        # We expect the PID column to contain the ID of this process
        assert lsof_data[1] == str(pid)
        # We expect an exclusive write lock to be set for this process
        assert lsof_data[3].find('W') != -1


@mock.patch("Notify.sdlog.error")
@mock.patch("Notify.sdlog.info")
def test_updater_lock_prevents_notifier(mocked_info, mocked_error):
    """
    Test whether an exlusive lock on the updater lock file prevents the notifier
    from launching (so it does not come up when the user is in the process of
    updating).
    """
    with TemporaryDirectory() as tmpdir:
        notify.LOCK_FILE_LAUNCHER = os.path.join(tmpdir, "sdw-launcher.lock")
        updater.LOCK_FILE = os.path.join(tmpdir, "sdw-launcher.lock")
        lh = updater.obtain_lock()  # noqa: F841

        # We're in the same process, so obtaining an additional lock would
        # always succeed. We use the multiprocessing module to run the function
        # as a separate process.
        p = Pool(processes=1)
        lock_result = p.apply(notify.can_obtain_updater_lock)
        p.close()
        assert lock_result is False


@mock.patch("Notify.sdlog.error")
@mock.patch("Notify.sdlog.info")
def test_no_updater_lock_has_no_effect(mocked_info, mocked_error):
    """
    Test whether we _can_ run the notifier when we don't have a lock
    on the updater.
    """
    with TemporaryDirectory() as tmpdir:
        notify.LOCK_FILE_LAUNCHER = os.path.join(tmpdir, "sdw-launcher.lock")
        lock_result = notify.can_obtain_updater_lock()
        assert lock_result is True
