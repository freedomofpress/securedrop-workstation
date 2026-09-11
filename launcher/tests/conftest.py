import os
import socket
import tempfile

import pytest

import sdw_updater.Updater
from sdw_updater.Updater import SD_UPDATER_TAG


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
MOCK_SDW_BASE_TEMPLATE = "sd-base-debian-XX"
MOCK_SDW_TEMPLATES = [
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

# The admin-only TemplateVM and AppVM (also tagged `sd-workstation`).
MOCK_SDW_ADMIN_TEMPLATE = "sd-admin-debian-XX"
MOCK_SDW_ADMIN_APPVMS = {
    "sd-admin": MOCK_SDW_ADMIN_TEMPLATE,
}


def _make_mocked_qubes_app(mocker, journalist: bool, admin: bool):
    """
    Build a mock Qubes app with the journalist qubes, the admin qubes, or both.

    The Fedora template and the sys-* VMs it backs are always present.
    """
    from qubesadmin.tests import mock_app
    from qubesadmin.tests.mock_app import MockQube, QubesTestWrapper

    # The mock only registers `admin.vm.tag.Get` calls for tags it knows about,
    # so register our tags to allow `"sd-workstation" in vm.tags` checks against
    # untagged VMs (e.g. the Fedora template).
    for tag in (SD_TAG, SD_UPDATER_TAG):
        if tag not in mock_app.POSSIBLE_TAGS:
            mock_app.POSSIBLE_TAGS.append(tag)

    class MockQubesWorkstation(QubesTestWrapper):
        def __init__(self):
            super().__init__()

            templates = []
            appvms = {}
            if journalist:
                self._qubes[MOCK_SDW_BASE_TEMPLATE] = MockQube(
                    name=MOCK_SDW_BASE_TEMPLATE,
                    qapp=self,
                    klass="TemplateVM",
                    netvm="",
                    tags=[SD_TAG],
                )
                templates.extend(MOCK_SDW_TEMPLATES)
                appvms.update(MOCK_SDW_APPVMS)
            if admin:
                templates.append(MOCK_SDW_ADMIN_TEMPLATE)
                appvms.update(MOCK_SDW_ADMIN_APPVMS)

            # 1. Create the SecureDrop templates (tagged `sd-workstation`)
            for template_name in templates:
                self._qubes[template_name] = MockQube(
                    name=template_name,
                    qapp=self,
                    klass="TemplateVM",
                    netvm="",
                    tags=[SD_TAG, SD_UPDATER_TAG],
                )

            # 2. Create the Fedora template backing the sys-* VMs (NOT tagged)
            self._qubes[MOCK_FEDORA_TEMPLATE] = MockQube(
                name=MOCK_FEDORA_TEMPLATE,
                qapp=self,
                klass="TemplateVM",
                netvm="",
            )

            # 3. Create the SecureDrop app qubes (tagged `sd-workstation`)
            for qube_name, template_name in appvms.items():
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

    # return the mock to allow for further modifications in tests
    return mock_qubes_app


@pytest.fixture
def mocked_journalist_qubes(mocker):
    """A journalist workstation: no admin qubes."""
    return _make_mocked_qubes_app(mocker, journalist=True, admin=False)


@pytest.fixture
def mocked_admin_qubes(mocker):
    """An admin-only workstation: no journalist qubes."""
    return _make_mocked_qubes_app(mocker, journalist=False, admin=True)


@pytest.fixture
def mocked_combined_qubes(mocker):
    """A workstation with both the journalist and the admin qubes."""
    return _make_mocked_qubes_app(mocker, journalist=True, admin=True)
