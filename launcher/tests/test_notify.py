import imp
import os
import subprocess

from tempfile import TemporaryDirectory
relpath_notify = "../sdw_notify/Notify.py"
path_to_script = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), relpath_notify
)


notify = imp.load_source("Notify", path_to_script)


def test_notify_lock():
    with TemporaryDirectory() as tmpdir:
        notify.LOCK_FILE_NOTIFIER = os.path.join(tmpdir, "sdw-launcher.lock")
        pid = os.getpid()
        lh = notify.obtain_notify_lock()  # noqa: F841
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
