import os
import time
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
import qubesadmin
from qubesadmin.app import VMCollection
from qubesadmin.tests.mock_app import MockQube, QubesTestWrapper

from securedrop_manage import main as manage
from tests.base import SD_TAG

if TYPE_CHECKING:
    from qubesadmin.vm import QubesVM


@pytest.fixture
def template_upgrades_available(mocker: Any) -> None:
    """
    Pretend that there are template upgrades available
    """
    mocker.patch.object(
        manage.template_upgrade_handler, "template_upgrades_skipped", return_value=False
    )


@pytest.fixture
def cleanup_prohibit_start() -> Generator:
    """
    Ensure cleanup in case of a test failure when testing with prohibit-start feature
    """
    yield
    for qube in qubesadmin.Qubes().domains:
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
def mock_qubes_app(mocker: Any) -> QubesTestWrapper:
    """
    Simulate a qubesadmin.Qubes() object called by securedrop_manage
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
    mocker.patch.object(manage, "Qubes", return_value=mock_qubes_app)

    # yield the mock to allow for further modifications in tests
    return mock_qubes_app


def test_is_managed() -> None:
    assert manage.is_managed("sd-app")


@pytest.fixture
def let_sd_viewer_preloads_settle(all_vms: VMCollection) -> Any:
    """
    Wait for preloaded qubes to be fully settled before next test

    The way to set preloaded disposables in Qubes (preload-dispvm-max feature)
    is non-blocking. This means that disposables may still be in the process
    of being created. This teardown makes sure they are ready for the next
    test (assumed sequential).
    """
    yield

    all_vms.refresh_cache(force=True)
    max_preloads = int(all_vms["dom0"].features["preload-dispvm-max"])
    expected_preload_names = set(all_vms["sd-viewer"].features.get("preload-dispvm", "").split())

    # OpenQA takes much longer to start/stop qubes
    timeout = 90 if os.environ.get("CI") else 30

    for attempt in range(timeout):
        all_vms.refresh_cache(force=True)

        # Preload completeness needs multiple conditions to be true
        ready_preloads = [
            p
            for p in all_vms["sd-viewer"].appvms
            if p.is_running()
            and p.features.get("preload-dispvm-completed", "") != ""
            and getattr(p, "is_preload")
            and p.name in expected_preload_names  # ignore "zombie" preloads (qubes-issues#11129)
        ]
        if len(ready_preloads) == max_preloads:
            return

        time.sleep(1)

    pytest.fail("Failed to clean up preloaded disposables")


@pytest.mark.run_alone  # Otherwise it would interfere in parallel tests
@pytest.mark.provisioning
def test_suppress_preloaded_disposables(let_sd_viewer_preloads_settle: Any) -> None:
    def get_preloaded_qubes() -> list["QubesVM"]:
        return list(filter(lambda q: getattr(q, "is_preload", False), app.domains))

    app = qubesadmin.Qubes()

    # Save num of preloaded disposables
    old_preload_dispvm_max = int(app.domains["dom0"].features["preload-dispvm-max"])
    old_preload_disposables = get_preloaded_qubes()
    assert old_preload_dispvm_max == len(old_preload_disposables) != 0

    with manage.suppress_preloaded_disposables():
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


@pytest.mark.run_alone  # Otherwise it would interfere in parallel tests
class TestTemplateUpgradesAvailable:
    def test_template_upgrade_handler(
        self,
        template_upgrades_available: None,
        suppress_policies: None,
        cleanup_prohibit_start: None,
    ) -> None:
        # Start with an SDW qube
        app = qubesadmin.Qubes()
        sd_proxy = app.domains["sd-proxy"]
        if sd_proxy.is_halted():
            sd_proxy.start()

        with manage.template_upgrade_handler():
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
        mock_qubes_app: QubesTestWrapper,
        mocker: Any,
    ) -> None:
        # Patch securedrop-manage to expect a certain Debian version
        mocker.patch.object(manage, "DEBIAN_VERSION", expected_ver)

        # Make templates return report a specific 'os-version' without
        # actually messing with the system
        for qube in mock_qubes_app.domains:
            # Just tell is tagged as 'sd-workstation'
            if qube.klass == "TemplateVM" and SD_TAG in qube.tags:
                mock_qubes_app.expected_calls[
                    (qube.name, "admin.vm.feature.Get", "os-version", None)
                ] = b"0\x00" + template_ver.encode()

        upgrade_handler = manage.template_upgrade_handler()
        assert upgrade_handler.template_upgrades_skipped() == should_upgrades_be_skipped


def test_legacy_config_is_migrated(tmp_path: Path) -> None:
    CONFIG_PATH: Path = tmp_path / "new_config"
    LEGACY_CONFIG_PATH: Path = tmp_path / "old_config"

    CONFIG_PATH.mkdir()
    LEGACY_CONFIG_PATH.mkdir()

    config_file: Path = LEGACY_CONFIG_PATH / "config.json"
    key_file: Path = LEGACY_CONFIG_PATH / "sd-journalist.sec"
    dummy_file: Path = LEGACY_CONFIG_PATH / "nocopy.txt"

    new_config_file: Path = CONFIG_PATH / "config.json"
    new_key_file: Path = CONFIG_PATH / "sd-journalist.sec"
    new_dummy_file: Path = CONFIG_PATH / "nocopy.txt"

    for source_file in [config_file, key_file, dummy_file]:
        source_file.write_text(str(source_file))

    manage.move_legacy_config(LEGACY_CONFIG_PATH, CONFIG_PATH)

    # config files should be moved
    for source_file in [config_file, key_file]:
        assert not source_file.exists()

    # other files should not be moved
    assert dummy_file.exists()

    # only the config files should be present in new location
    for source_file in [new_config_file, new_key_file]:
        assert source_file.exists()

    # other files should not be moved
    assert not new_dummy_file.exists()
