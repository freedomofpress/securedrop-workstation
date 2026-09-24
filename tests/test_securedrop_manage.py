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


def test_get_installed_product(tmp_path: Path) -> None:
    with pytest.raises(manage.ManageException):
        # nothing installed in our tmp_path yet
        manage.get_installed_product(tmp_path)

    (tmp_path / "admin-workstation.json").write_text("{}")
    assert manage.get_installed_product(tmp_path) is manage.Product.ADMIN

    (tmp_path / "journalist-workstation.json").write_text("{}")
    assert manage.get_installed_product(tmp_path) is manage.Product.ALL

    (tmp_path / "admin-workstation.json").unlink()
    assert manage.get_installed_product(tmp_path) is manage.Product.JOURNALIST


@pytest.mark.parametrize(
    ("requested", "installed", "expected"),
    [
        # Default to the only installed product
        (None, manage.Product.JOURNALIST, manage.Product.JOURNALIST),
        (None, manage.Product.ADMIN, manage.Product.ADMIN),
        # Explicitly requesting an installed product
        (manage.Product.JOURNALIST, manage.Product.JOURNALIST, manage.Product.JOURNALIST),
        (manage.Product.JOURNALIST, manage.Product.ALL, manage.Product.JOURNALIST),
        (manage.Product.ADMIN, manage.Product.ALL, manage.Product.ADMIN),
        # --all selects everything installed
        (manage.Product.ALL, manage.Product.JOURNALIST, manage.Product.JOURNALIST),
        (manage.Product.ALL, manage.Product.ALL, manage.Product.ALL),
        # Errors
        (None, manage.Product.ALL, None),
        (manage.Product.ADMIN, manage.Product.JOURNALIST, None),
        (manage.Product.JOURNALIST, manage.Product.ADMIN, None),
    ],
)
def test_select_product(
    requested: manage.Product | None, installed: manage.Product, expected: manage.Product | None
) -> None:
    if expected is None:
        with pytest.raises(manage.ManageException):
            manage.select_product(requested, installed)
    else:
        assert manage.select_product(requested, installed) is expected


@pytest.fixture
def fake_qubes(tmp_path: Path, mocker: Any, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """
    Stand in for vault and sd-admin with local directories: a fake qvm-run on PATH runs
    the command locally, and the config paths on both ends point into tmp_path.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    qvm_run = bin_dir / "qvm-run"
    # qvm-run --pass-io <vm> <command>
    qvm_run.write_text('#!/bin/sh\nexec sh -c "$3"\n')
    qvm_run.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")

    usb = tmp_path / "TailsData/securedrop-admin"
    sd_admin = tmp_path / "sd-admin/.config/securedrop-admin"
    usb.mkdir(parents=True)
    sd_admin.parent.mkdir(parents=True)
    mocker.patch.object(manage, "TAILS_ADMIN_CONFIG_PATH", usb)
    mocker.patch.object(manage, "SD_ADMIN_CONFIG_PATH", str(sd_admin))
    mocker.patch.object(manage, "Qubes").return_value.domains = [manage.SD_ADMIN_VM, "vault"]
    return {"usb": usb, "sd_admin": sd_admin}


def _start_vault_is_skipped(mocker: Any) -> None:
    # qvm-start vault is fire-and-forget; don't try to run it
    real_popen = manage.subprocess.Popen

    def popen(args: list[str], **kwargs: Any) -> Any:
        if args[0] == "qvm-start":
            return mocker.Mock()
        return real_popen(args, **kwargs)

    mocker.patch.object(manage.subprocess, "Popen", side_effect=popen)


class TestImportAdminConfig:
    def test_copies_config_into_sd_admin(self, fake_qubes: dict[str, Path], mocker: Any) -> None:
        _start_vault_is_skipped(mocker)
        usb = fake_qubes["usb"]
        (usb / "site-specific").write_text("app_hostname: app\n")
        (usb / "app-journalist.auth_private").write_text("abc:descriptor:x25519:key\n")
        mocker.patch("builtins.input", return_value="y")

        manage.import_admin_config()

        sd_admin = fake_qubes["sd_admin"]
        assert sorted(p.name for p in sd_admin.iterdir()) == [
            "app-journalist.auth_private",
            "site-specific",
        ]
        assert (sd_admin / "site-specific").read_text() == "app_hostname: app\n"
        assert sd_admin.stat().st_mode & 0o777 == 0o700
        assert (sd_admin / "site-specific").stat().st_mode & 0o777 == 0o600
        assert not Path(f"{sd_admin}.new").exists()

    def test_requires_sd_admin(self, fake_qubes: dict[str, Path], mocker: Any) -> None:
        mocker.patch.object(manage, "Qubes").return_value.domains = ["vault"]
        with pytest.raises(manage.ManageException, match="does not exist"):
            manage.import_admin_config()

    def test_rejects_journalist_usb(self, fake_qubes: dict[str, Path], mocker: Any) -> None:
        _start_vault_is_skipped(mocker)
        (fake_qubes["usb"] / "app-journalist.auth_private").write_text("abc\n")
        mocker.patch("builtins.input", return_value="y")
        copy = mocker.patch.object(manage, "copy_admin_config")

        with pytest.raises(manage.ManageException, match="Journalist Workstation USB"):
            manage.import_admin_config()
        copy.assert_not_called()

    def test_rejects_locked_usb(self, fake_qubes: dict[str, Path], mocker: Any) -> None:
        _start_vault_is_skipped(mocker)
        fake_qubes["usb"].rmdir()
        mocker.patch("builtins.input", return_value="y")

        with pytest.raises(manage.ManageException, match="No securedrop-admin configuration"):
            manage.import_admin_config()

    def test_keeps_existing_config_unless_confirmed(
        self, fake_qubes: dict[str, Path], mocker: Any
    ) -> None:
        fake_qubes["sd_admin"].mkdir()
        (fake_qubes["sd_admin"] / "site-specific").write_text("existing\n")
        mocker.patch("builtins.input", return_value="n")
        copy = mocker.patch.object(manage, "copy_admin_config")

        manage.import_admin_config()

        copy.assert_not_called()
        assert (fake_qubes["sd_admin"] / "site-specific").read_text() == "existing\n"

    def test_failed_transfer_leaves_existing_config(
        self, fake_qubes: dict[str, Path], mocker: Any
    ) -> None:
        fake_qubes["sd_admin"].mkdir()
        (fake_qubes["sd_admin"] / "site-specific").write_text("existing\n")
        # tar fails on the vault end
        mocker.patch.object(manage, "TAILS_ADMIN_CONFIG_PATH", fake_qubes["usb"] / "missing")

        with pytest.raises(manage.ManageException, match="Error copying"):
            manage.copy_admin_config()

        assert (fake_qubes["sd_admin"] / "site-specific").read_text() == "existing\n"
        assert not Path(f"{fake_qubes['sd_admin']}.new").exists()
