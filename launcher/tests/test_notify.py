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
        full_cmd = ["lslocks", "-n", "-p", str(pid), "-o", "MODE,PATH"]
        lock_data = subprocess.check_output(full_cmd).decode("utf-8").strip().split()

        # Validate basic output matches the expected format
        assert len(lock_data) == 2
        # Validate that we have a write lock on the notifier lock file
        assert lock_data[0] == 'WRITE'
