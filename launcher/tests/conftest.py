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


SD_TAG = "sd-workstation"
MOCK_FEDORA_TEMPLATE = "fedora-XX-xfce"

# SecureDrop-managed TemplateVMs, all tagged `sd-workstation`.
MOCK_SDW_TEMPLATES = [
    "sd-base-debian-XX",
    "sd-inbox-debian-XX",
    "sd-viewer-debian-XX",
]

# SecureDrop-managed AppVMs (tagged) mapped to their template.
MOCK_SDW_APPVMS = {
    "sd-app": "sd-inbox-debian-XX",
    "sd-log": "sd-inbox-debian-XX",
    "sd-proxy": "sd-inbox-debian-XX",
    "sd-gpg": "sd-inbox-debian-XX",
    "sd-viewer": "sd-viewer-debian-XX",
    "sd-devices": "sd-viewer-debian-XX",
    "sd-printers": "sd-viewer-debian-XX",
}


@pytest.fixture
def mocked_qubes_app(mocker):
    from qubesadmin.tests import mock_app
    from qubesadmin.tests.mock_app import MockQube, QubesTestWrapper

    # The mock only registers `admin.vm.tag.Get` calls for tags it knows about,
    # so register `sd-workstation` to allow `"sd-workstation" in vm.tags` checks
    # against untagged VMs (e.g. the Fedora template).
    if SD_TAG not in mock_app.POSSIBLE_TAGS:
        mock_app.POSSIBLE_TAGS.append(SD_TAG)

    class MockQubesWorkstation(QubesTestWrapper):
        def __init__(self):
            super().__init__()

            # 1. Create the SecureDrop templates (tagged `sd-workstation`)
            for template_name in MOCK_SDW_TEMPLATES:
                self._qubes[template_name] = MockQube(
                    name=template_name,
                    qapp=self,
                    klass="TemplateVM",
                    netvm="",
                    tags=[SD_TAG],
                )

            # 2. Create the Fedora template backing the sys-* VMs (NOT tagged)
            self._qubes[MOCK_FEDORA_TEMPLATE] = MockQube(
                name=MOCK_FEDORA_TEMPLATE,
                qapp=self,
                klass="TemplateVM",
                netvm="",
            )

            # 3. Create the SecureDrop app qubes (tagged `sd-workstation`)
            for qube_name, template_name in MOCK_SDW_APPVMS.items():
                MockQube(
                    qube_name,
                    self,
                    template=template_name,
                    tags=[SD_TAG],
                )

            # 4. Create the sys-* VMs (NOT tagged) based on the Fedora template
            for sys_vm in sdw_updater.Updater.SYSTEM_VMS:
                MockQube(
                    sys_vm,
                    self,
                    template=MOCK_FEDORA_TEMPLATE,
                )

            # 5. TODO Lastly create the disposables

            self.update_vm_calls()

    mock_qubes_app = MockQubesWorkstation()

    # Patch "Qubes()" to allow tests to run on this fake mock
    mocker.patch("qubesadmin.Qubes").return_value = mock_qubes_app

    # yield the mock to allow for further modifications in tests
    return mock_qubes_app
