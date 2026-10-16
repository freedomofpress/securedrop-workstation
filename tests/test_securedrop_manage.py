import os
import time
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
import qubesadmin
from qubesadmin.app import VMCollection
from qubesadmin.tests.mock_app import MockQube, QubesTestWrapper

from securedrop_manage import configure
from securedrop_manage import main as manage
from tests.base import SD_TAG
from tests.markers import needs_journalist

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


@needs_journalist
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
@needs_journalist
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
@needs_journalist
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


@pytest.mark.parametrize(
    ("installed", "argv", "expected"),
    [
        # only one product installed, --target defaults to it
        (manage.Product.JOURNALIST, ["--apply"], manage.Product.JOURNALIST),
        (manage.Product.ADMIN, ["--apply"], manage.Product.ADMIN),
        (
            manage.Product.JOURNALIST,
            ["--apply", "--target", "journalist"],
            manage.Product.JOURNALIST,
        ),
        # only one product installed, --target all means just that product
        (manage.Product.JOURNALIST, ["--apply", "--target", "all"], manage.Product.JOURNALIST),
        (manage.Product.ADMIN, ["--apply", "--target", "all"], manage.Product.ADMIN),
        # both installed, --target must be explicit
        (manage.Product.ALL, ["--apply", "--target", "journalist"], manage.Product.JOURNALIST),
        (manage.Product.ALL, ["--apply", "--target", "admin"], manage.Product.ADMIN),
        (manage.Product.ALL, ["--apply", "--target", "all"], manage.Product.ALL),
    ],
)
def test_parse_args_target(
    mocker: Any,
    monkeypatch: pytest.MonkeyPatch,
    installed: "manage.Product",
    argv: list[str],
    expected: "manage.Product",
) -> None:
    mocker.patch.object(manage, "get_installed_product", return_value=installed)
    monkeypatch.setattr("sys.argv", ["securedrop-manage", *argv])
    args = manage.parse_args()
    assert args.product is expected


@pytest.mark.parametrize(
    ("installed", "argv"),
    [
        # both installed, but no --target given
        (manage.Product.ALL, ["--apply"]),
        # --target for a product that isn't installed
        (manage.Product.JOURNALIST, ["--apply", "--target", "admin"]),
        (manage.Product.ADMIN, ["--apply", "--target", "journalist"]),
    ],
)
def test_parse_args_target_invalid(
    mocker: Any, monkeypatch: pytest.MonkeyPatch, installed: "manage.Product", argv: list[str]
) -> None:
    mocker.patch.object(manage, "get_installed_product", return_value=installed)
    monkeypatch.setattr("sys.argv", ["securedrop-manage", *argv])
    with pytest.raises(SystemExit):
        manage.parse_args()


@pytest.fixture
def fake_qubes(tmp_path: Path, mocker: Any, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """
    Stand in for vault and sd-admin with local directories: a fake qvm-run on PATH runs
    the command locally, and the paths on both ends point into tmp_path.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    qvm_run = bin_dir / "qvm-run"
    # qvm-run [--pass-io] <vm> <command>...
    qvm_run.write_text(
        '#!/bin/sh\nwhile [ "${1#-}" != "$1" ]; do shift; done\nshift\nexec sh -c "$*"\n'
    )
    qvm_run.chmod(0o755)
    # shipped in sd-admin by securedrop-admin-qubes; record how it's called
    set_site_specific = bin_dir / configure.SET_SITE_SPECIFIC
    set_site_specific_log = tmp_path / "set-site-specific.log"
    set_site_specific.write_text(f'#!/bin/sh\necho "$@" >> "{set_site_specific_log}"\n')
    set_site_specific.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")

    usb = tmp_path / "TailsData/securedrop-admin"
    usb_ssh = tmp_path / "TailsData/openssh-client"
    sd_admin = tmp_path / "sd-admin/.config/securedrop-admin"
    sd_admin_ssh = tmp_path / "sd-admin/.ssh"
    staging = tmp_path / "sd-admin/.securedrop-admin-import"
    usb.mkdir(parents=True)
    usb_ssh.mkdir()
    (usb_ssh / "id_rsa").write_text("private\n")
    (usb_ssh / "id_rsa.pub").write_text("public\n")
    sd_admin.parent.mkdir(parents=True)
    mocker.patch.object(configure, "TAILS_ADMIN_CONFIG_PATH", usb)
    mocker.patch.object(configure, "TAILS_SSH_PATH", usb_ssh)
    mocker.patch.object(configure, "SD_ADMIN_CONFIG_PATH", str(sd_admin))
    mocker.patch.object(configure, "SD_ADMIN_SSH_PATH", str(sd_admin_ssh))
    mocker.patch.object(configure, "SD_ADMIN_STAGING_PATH", str(staging))
    mocker.patch.object(configure, "Qubes").return_value.domains = [configure.SD_ADMIN_VM, "vault"]
    return {
        "usb": usb,
        "usb_ssh": usb_ssh,
        "sd_admin": sd_admin,
        "sd_admin_ssh": sd_admin_ssh,
        "staging": staging,
        "set_site_specific": set_site_specific,
        "set_site_specific_log": set_site_specific_log,
    }


def _start_vault_is_skipped(mocker: Any) -> None:
    # qvm-start vault is fire-and-forget; don't try to run it
    real_popen = configure.subprocess.Popen

    def popen(args: list[str], **kwargs: Any) -> Any:
        if args[0] == "qvm-start":
            return mocker.Mock()
        return real_popen(args, **kwargs)

    mocker.patch.object(configure.subprocess, "Popen", side_effect=popen)


class TestConfigureAdmin:
    @pytest.fixture(autouse=True)
    def _admin_installed(self, mocker: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        mocker.patch.object(manage.os, "geteuid", return_value=1000)
        mocker.patch.object(manage, "get_installed_product", return_value=manage.Product.ADMIN)
        monkeypatch.setattr("sys.argv", ["securedrop-manage", "--configure"])

    def test_validates_before_import(self, mocker: Any) -> None:
        calls = mocker.Mock()
        mocker.patch.object(manage, "validate_config", calls.validate_config)
        mocker.patch.object(manage, "import_admin_config", calls.import_admin_config)

        manage.main()

        assert calls.mock_calls == [
            mocker.call.validate_config(manage.CONFIG_PATH, manage.Product.ADMIN),
            mocker.call.import_admin_config(),
        ]

    def test_invalid_config_skips_import(self, mocker: Any) -> None:
        mocker.patch.object(
            manage, "validate_config", side_effect=manage.ManageException("invalid")
        )
        import_admin_config = mocker.patch.object(manage, "import_admin_config")

        with pytest.raises(manage.ManageException):
            manage.main()
        import_admin_config.assert_not_called()


class TestImportAdminConfig:
    def test_copies_config_into_sd_admin(self, fake_qubes: dict[str, Path], mocker: Any) -> None:
        _start_vault_is_skipped(mocker)
        usb = fake_qubes["usb"]
        (usb / "site-specific").write_text("app_hostname: app\n")
        (usb / "app-journalist.auth_private").write_text("abc:descriptor:x25519:key\n")
        (usb / "app-journalist.auth_private").chmod(0o644)
        mocker.patch("builtins.input", return_value="y")

        configure.import_admin_config()

        sd_admin = fake_qubes["sd_admin"]
        assert sorted(p.name for p in sd_admin.iterdir()) == [
            "app-journalist.auth_private",
            "site-specific",
        ]
        assert (sd_admin / "site-specific").read_text() == "app_hostname: app\n"
        assert sd_admin.stat().st_mode & 0o777 == 0o700
        for path in sd_admin.iterdir():
            assert path.stat().st_mode & 0o777 == 0o600

        ssh = fake_qubes["sd_admin_ssh"]
        assert ssh.stat().st_mode & 0o777 == 0o700
        assert (ssh / "id_rsa").read_text() == "private\n"
        assert (ssh / "id_rsa").stat().st_mode & 0o777 == 0o600
        assert (ssh / "id_rsa.pub").read_text() == "public\n"
        assert (ssh / "id_rsa.pub").stat().st_mode & 0o777 == 0o644

        assert not fake_qubes["staging"].exists()

    def test_copies_only_files(self, fake_qubes: dict[str, Path]) -> None:
        (fake_qubes["usb"] / "site-specific").write_text("app_hostname: app\n")
        (fake_qubes["usb"] / "subdir").mkdir()

        assert configure.copy_admin_config() == ["site-specific"]

    def test_replaces_leftover_staging(self, fake_qubes: dict[str, Path]) -> None:
        (fake_qubes["usb"] / "site-specific").write_text("app_hostname: app\n")
        leftover = fake_qubes["staging"] / "config"
        leftover.mkdir(parents=True)
        (leftover / "stale").write_text("stale\n")

        assert configure.copy_admin_config() == ["site-specific"]

    def test_removes_staging_on_exception(self, fake_qubes: dict[str, Path], mocker: Any) -> None:
        (fake_qubes["usb"] / "site-specific").write_text("app_hostname: app\n")

        def pipe_file(source: str, destination: str) -> None:
            assert fake_qubes["staging"].exists()
            raise KeyboardInterrupt

        mocker.patch.object(configure, "_pipe_admin_file", side_effect=pipe_file)

        with pytest.raises(KeyboardInterrupt):
            configure.copy_admin_config()
        assert not fake_qubes["staging"].exists()

    def test_rejects_missing_ssh_keys(self, fake_qubes: dict[str, Path], mocker: Any) -> None:
        _start_vault_is_skipped(mocker)
        (fake_qubes["usb"] / "site-specific").write_text("app_hostname: app\n")
        (fake_qubes["usb_ssh"] / "id_rsa").unlink()
        mocker.patch("builtins.input", return_value="y")
        copy = mocker.patch.object(configure, "copy_admin_config")

        with pytest.raises(manage.ManageException, match="No SSH keys"):
            configure.import_admin_config()
        copy.assert_not_called()

    def test_sets_config_path(self, fake_qubes: dict[str, Path]) -> None:
        (fake_qubes["usb"] / "site-specific").write_text("app_hostname: app\n")

        configure.copy_admin_config()

        staged_site_specific = fake_qubes["staging"] / "config/site-specific"
        assert fake_qubes["set_site_specific_log"].read_text() == (
            f"--file {staged_site_specific} config_path {fake_qubes['sd_admin']}\n"
        )

    def test_skips_config_path_without_set_site_specific(
        self, fake_qubes: dict[str, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        (fake_qubes["usb"] / "site-specific").write_text("app_hostname: app\n")
        # older securedrop-admin-qubes without the script
        fake_qubes["set_site_specific"].unlink()

        assert configure.copy_admin_config() == ["site-specific"]

        assert (fake_qubes["sd_admin"] / "site-specific").read_text() == "app_hostname: app\n"
        assert not fake_qubes["set_site_specific_log"].exists()
        assert "not updating config_path" in capsys.readouterr().out

    def test_requires_sd_admin(self, fake_qubes: dict[str, Path], mocker: Any) -> None:
        mocker.patch.object(configure, "Qubes").return_value.domains = ["vault"]
        with pytest.raises(manage.ManageException, match="does not exist"):
            configure.import_admin_config()

    def test_rejects_journalist_usb(self, fake_qubes: dict[str, Path], mocker: Any) -> None:
        _start_vault_is_skipped(mocker)
        (fake_qubes["usb"] / "app-journalist.auth_private").write_text("abc\n")
        mocker.patch("builtins.input", return_value="y")
        copy = mocker.patch.object(configure, "copy_admin_config")

        with pytest.raises(manage.ManageException, match="Journalist Workstation USB"):
            configure.import_admin_config()
        copy.assert_not_called()

    def test_rejects_locked_usb(self, fake_qubes: dict[str, Path], mocker: Any) -> None:
        _start_vault_is_skipped(mocker)
        fake_qubes["usb"].rmdir()
        mocker.patch("builtins.input", return_value="y")

        with pytest.raises(manage.ManageException, match="No securedrop-admin configuration"):
            configure.import_admin_config()

    def test_keeps_existing_config_unless_confirmed(
        self, fake_qubes: dict[str, Path], mocker: Any
    ) -> None:
        fake_qubes["sd_admin"].mkdir()
        (fake_qubes["sd_admin"] / "site-specific").write_text("existing\n")
        mocker.patch("builtins.input", return_value="n")
        copy = mocker.patch.object(configure, "copy_admin_config")

        configure.import_admin_config()

        copy.assert_not_called()
        assert (fake_qubes["sd_admin"] / "site-specific").read_text() == "existing\n"

    def test_keeps_existing_ssh_key_unless_confirmed(
        self, fake_qubes: dict[str, Path], mocker: Any
    ) -> None:
        fake_qubes["sd_admin_ssh"].mkdir()
        (fake_qubes["sd_admin_ssh"] / "id_rsa").write_text("existing\n")
        mocker.patch("builtins.input", return_value="n")
        copy = mocker.patch.object(configure, "copy_admin_config")

        configure.import_admin_config()

        copy.assert_not_called()

    def test_failed_transfer_leaves_existing_config(
        self, fake_qubes: dict[str, Path], mocker: Any
    ) -> None:
        fake_qubes["sd_admin"].mkdir()
        (fake_qubes["sd_admin"] / "site-specific").write_text("existing\n")
        (fake_qubes["usb"] / "site-specific").write_text("app_hostname: app\n")
        # reading the last file fails on the vault end, after the others were copied
        (fake_qubes["usb_ssh"] / "id_rsa.pub").unlink()

        with pytest.raises(manage.ManageException, match="Error copying"):
            configure.copy_admin_config()

        assert (fake_qubes["sd_admin"] / "site-specific").read_text() == "existing\n"
        assert not fake_qubes["sd_admin_ssh"].exists()
        assert not fake_qubes["staging"].exists()

    def test_failed_listing_leaves_existing_config(
        self, fake_qubes: dict[str, Path], mocker: Any
    ) -> None:
        fake_qubes["sd_admin"].mkdir()
        (fake_qubes["sd_admin"] / "site-specific").write_text("existing\n")
        mocker.patch.object(configure, "TAILS_ADMIN_CONFIG_PATH", fake_qubes["usb"] / "missing")

        with pytest.raises(manage.ManageException, match="Error listing"):
            configure.copy_admin_config()

        assert (fake_qubes["sd_admin"] / "site-specific").read_text() == "existing\n"
        assert not fake_qubes["staging"].exists()

    def test_failed_install_leaves_existing_config(self, fake_qubes: dict[str, Path]) -> None:
        fake_qubes["sd_admin"].mkdir()
        (fake_qubes["sd_admin"] / "site-specific").write_text("existing\n")
        (fake_qubes["usb"] / "site-specific").write_text("app_hostname: app\n")
        # securedrop-set-site-specific fails on the sd-admin end
        fake_qubes["set_site_specific"].write_text("#!/bin/sh\nexit 1\n")

        with pytest.raises(manage.ManageException, match="Error installing"):
            configure.copy_admin_config()

        assert (fake_qubes["sd_admin"] / "site-specific").read_text() == "existing\n"
        assert not fake_qubes["sd_admin_ssh"].exists()
        assert not fake_qubes["staging"].exists()
