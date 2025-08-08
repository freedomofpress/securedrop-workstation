import os
import socket
import tempfile

import pytest


@pytest.fixture
def tmpdir():
    """Run the test in a temporary directory"""
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory(prefix="updater") as tmpdir:
        os.chdir(tmpdir)
        yield tmpdir
        os.chdir(cwd)


skip_in_dom0 = pytest.mark.skipif(
    socket.gethostname() == "dom0",
    reason="Test cannot be run in dom0",
)
