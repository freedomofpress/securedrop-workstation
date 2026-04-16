import os
import socket
import tempfile

import pytest

import sdw_updater.Updater


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
