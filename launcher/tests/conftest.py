import os
import socket
import tempfile

import pytest

import sdw_updater.Updater


@pytest.fixture
def mocked_qubes_vm_update(tmp_path, monkeypatch):
    """
    Factory fixture: call with stderr/stdout/retcode to register a
    fake qubes-vm-update process via a real script on PATH.
    All test data is written to files — no user content in script source.

    Assumption: `qubes-vm-update` is not called with /usr/bin/qubes-vm-update
    """

    def _mocked_qubes_vm_update(stderr="", stdout="", retcode=0):
        (tmp_path / "stdout.txt").write_text(stdout + "\n")
        (tmp_path / "stderr.txt").write_text(stderr + "\n")
        assert isinstance(retcode, int), "'retcode' must be an int"

        script = tmp_path / "qubes-vm-update"
        script.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "from pathlib import Path\n"
            "base = Path(__file__).parent\n"
            "sys.stdout.write((base / 'stdout.txt').read_text())\n"
            "sys.stderr.write((base / 'stderr.txt').read_text())\n"
            f"sys.exit({retcode})\n"
        )
        script.chmod(0o755)

    # Prepend script to path, so it get called instead of the real one
    monkeypatch.setenv("PATH", str(tmp_path), prepend=os.pathsep)

    return _mocked_qubes_vm_update


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


@pytest.fixture
def mocked_qubes_app(mocker):
    from qubesadmin.tests.mock_app import MockQube, QubesTestWrapper

    class MockQubesWorkstation(QubesTestWrapper):
        def __init__(self):
            super().__init__()

            # FIXME avoid using module under test. Obtain directly from main tests
            current_vms = sdw_updater.Updater._get_current_vms()

            # 1. create the templates
            for template_name in set(current_vms.values()):
                self._qubes[template_name] = MockQube(
                    name=template_name,
                    qapp=self,
                    klass="TemplateVM",
                    netvm="",
                )

            # 2. create the app qubes
            for qube_name, template_name in current_vms.items():
                MockQube(
                    qube_name,
                    self,
                    template=template_name,
                )

            # 3. TODO Lastly create the disposables

            self.update_vm_calls()

    mock_qubes_app = MockQubesWorkstation()

    # Patch "Qubes()" to allow tests to run on this fake mock
    mocker.patch("qubesadmin.Qubes").return_value = mock_qubes_app

    # yield the mock to allow for further modifications in tests
    return mock_qubes_app
