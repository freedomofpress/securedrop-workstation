import os
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
