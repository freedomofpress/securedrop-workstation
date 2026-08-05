import os
from collections.abc import Callable, Generator
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any

import pytest
import qubesadmin
from qubesadmin.tests.mock_app import MockQube, QubesTestWrapper

from tests.base import SD_TAG

if TYPE_CHECKING:
    from qubesadmin.app import VMCollection
    from qubesadmin.vm import QubesVM


@pytest.fixture
def sdw_admin(
    proj_root: Path,
    load_non_standard_module: Callable[[Path], ModuleType],
) -> ModuleType:
    """
    Equivalent to 'import sdw_admin', except as a pytest fixture.

    Workaround needed due to 'sdw-admin.py' having a non-pythonic '-' in its
    name and also not currently being in its own python module.
    """

    # FIXME this is a workaround. A better approach is to have sdw-admin in
    # a proper python module, trivially importable in tests. See #1750.
    return load_non_standard_module(proj_root / "files" / "sdw-admin.py")


@pytest.fixture
def template_upgrades_available(sdw_admin: Any, mocker: Any) -> None:
    """
    Pretend that there are template upgrades available
    """
    mock_func = mocker.MagicMock()
    mock_func.return_value = False
    sdw_admin.template_upgrade_handler.template_upgrades_skipped = mock_func


@pytest.fixture
def cleanup_prohibit_start(sdw_tagged_vms: "VMCollection") -> Generator:
    """
    Ensure cleanup in case of a test failure when testing with prohibit-start feature
    """
    yield
    for qube in sdw_tagged_vms:
        if qube.features.get("prohibit-start") == "disabled during set up":
            del qube.features["prohibit-start"]


@pytest.fixture
def suppress_policies() -> Generator:
    """
    Temporarily suppress SDW RPC services to prevent qube startup

    Qrexec services have the ability to start a qube. This may create
    race-conditions during a VM startup.

    NOTE: this might be https://github.com/freedomofpress/securedrop-workstation/issues/1751
    """

    policy_path = "/run/qubes/policy.d/20-sdw-override.policy"

    with open(policy_path, "w") as policy_f:
        policy_f.write(
            "securedrop.Log           *  @tag:sd-workstation   sd-log    deny        notify=no\n"
            "securedrop.GetSecretKeys *  sd-gpg                dom0      deny        notify=no\n"
            "securedrop.Proxy         *  sd-app                sd-proxy  deny        notify=no\n"
        )
    yield
    os.unlink(policy_path)


@pytest.fixture
def mock_qubes_app(sdw_admin: Any, mocker: Any) -> QubesTestWrapper:
    """
    Simulate a qubesadmin.Qubes() object called by sdw_admin
    """

    class MockQubesWorkstation(QubesTestWrapper):
        def __init__(self) -> None:
            super().__init__()

            # 1. A few SD-specific qubes
            sd_templates = [
                MockQube(
                    name="sd-debian-template-1",
                    qapp=self,
                    klass="TemplateVM",
                    netvm="",
                ),
                MockQube(
                    name="sd-debian-template-2",
                    qapp=self,
                    klass="TemplateVM",
                    netvm="",
                ),
            ]
            sd_app_qubes = [
                MockQube("sd-qube-1", self, template=sd_templates[0]),
                MockQube("sd-qube-2", self, template=sd_templates[1]),
            ]

            sd_disposables = [
                MockQube("sd-disp-1", self, klass="DisposableVM", template=sd_app_qubes[0]),
                MockQube("sd-disp-2", self, klass="DisposableVM", template=sd_app_qubes[1]),
            ]

            # Some default system qubes
            default_template = MockQube(
                name="default-template",
                qapp=self,
                klass="TemplateVM",
                netvm="",
            )
            default_app_qube = MockQube(
                name="default-qube",
                qapp=self,
                template=default_template,
                netvm="sys-firewall",
            )
            default_disp = MockQube(
                name="default-disp",
                qapp=self,
                template=default_app_qube,
                netvm="",
            )

            self.update_vm_calls()

            # Populate some expected qubesd queries

            # Report these with the SD tag
            for qube in sd_templates + sd_app_qubes + sd_disposables:
                self.expected_calls[(qube.name, "admin.vm.tag.Get", SD_TAG, None)] = b"0\x001"

            # Report these without the SD tag (if asked)
            for qube in [self.domains["dom0"], default_template, default_app_qube, default_disp]:
                self.expected_calls[(qube.name, "admin.vm.tag.Get", SD_TAG, None)] = b"0\x000"

    mock_qubes_app = MockQubesWorkstation()

    # Patch "Qubes()" to allow tests to run on this fake mock
    qubes_mock = mocker.MagicMock()
    qubes_mock.return_value = mock_qubes_app
    sdw_admin.Qubes = qubes_mock

    # yield the mock to allow for further modifications in tests
    return mock_qubes_app


def test_is_managed(sdw_admin: ModuleType) -> None:
    assert sdw_admin.is_managed("sd-app")


@pytest.mark.provisioning
def test_suppress_preloaded_disposables(sdw_admin: Any) -> None:
    def get_preloaded_qubes() -> list["QubesVM"]:
        return list(filter(lambda q: getattr(q, "is_preload", False), app.domains))

    app = qubesadmin.Qubes()

    # Save num of preloaded disposables
    old_preload_dispvm_max = int(app.domains["dom0"].features["preload-dispvm-max"])
    old_preload_disposables = get_preloaded_qubes()
    assert old_preload_dispvm_max == len(old_preload_disposables) != 0

    with sdw_admin.suppress_preloaded_disposables():
        app.domains.refresh_cache(force=True)

        # Ensure set back to 0 during contextual execution
        assert int(app.domains["dom0"].features["preload-dispvm-max"]) == 0

        # No preloaded disposables remain
        assert len(get_preloaded_qubes()) == 0

    # Value is set back to previous one
    app.domains.refresh_cache(force=True)
    new_preload_dispvm_max = int(app.domains["dom0"].features["preload-dispvm-max"])
    new_preload_disposables = get_preloaded_qubes()
    assert new_preload_disposables != old_preload_disposables
    assert new_preload_dispvm_max == int(app.domains["dom0"].features["preload-dispvm-max"])


class TestTemplateUpgradesAvailable:
    def test_template_upgrade_handler(
        self,
        sdw_admin: Any,
        template_upgrades_available: None,
        suppress_policies: None,
        cleanup_prohibit_start: None,
    ) -> None:
        # Start with an SDW qube
        app = qubesadmin.Qubes()
        sd_proxy = app.domains["sd-proxy"]
        if sd_proxy.is_halted():
            sd_proxy.start()

        with sdw_admin.template_upgrade_handler():
            # SDW qubes should have all be shut down
            assert sd_proxy.is_halted()

            # And they can no longer be started
            with pytest.raises(qubesadmin.exc.QubesException) as exc_info:
                sd_proxy.start()
            assert "Qube start is prohibited" in str(exc_info.value)

        # sd-proxy should start just fine (startup has been re-enabled)
        sd_proxy.start()

        # Shut down sd-proxy so it doesn't start sd-log through 'securedrop.Log'
        # after test finishes
        sd_proxy.shutdown()

    @pytest.mark.parametrize(
        ("template_ver", "expected_ver", "should_upgrades_be_skipped"),
        [
            ("11", "13", False),  # Version jump
            ("12", "13", False),  # Regular version bump
            ("13", "13", True),  # Same version; no upgrade needed
        ],
    )
    def test_template_upgrades_skipped(
        self,
        template_ver: str,
        expected_ver: str,
        should_upgrades_be_skipped: bool,
        sdw_admin: Any,
        mock_qubes_app: QubesTestWrapper,
    ) -> None:
        # Patch sdw-admin to expect a certain Debian version
        sdw_admin.DEBIAN_VERSION = expected_ver

        # Make templates return report a specific 'os-version' without
        # actually messing with the system
        for qube in mock_qubes_app.domains:
            # Just tell is tagged as 'sd-workstation'
            if qube.klass == "TemplateVM" and SD_TAG in qube.tags:
                mock_qubes_app.expected_calls[
                    (qube.name, "admin.vm.feature.Get", "os-version", None)
                ] = b"0\x00" + template_ver.encode()

        upgrade_handler = sdw_admin.template_upgrade_handler()
        assert upgrade_handler.template_upgrades_skipped() == should_upgrades_be_skipped
