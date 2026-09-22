"""
Integration tests for "securedrop-manage --configure"
"""

import json
import subprocess
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from securedrop_manage import main as manage

FAKE_JI_ADDRESS = "sdwfaketestonionaddressforintegrationtests22222222222222"
FAKE_JI_AUTH_TOKEN = "SDWFAKETESTAUTHTOKENFORINTEGRATIONTESTS2222222222222"
FAKE_JI_CONFIG = f"{FAKE_JI_ADDRESS}:descriptor:x25519:{FAKE_JI_AUTH_TOKEN}"

# intentionally not the defaults so we can assert they were set correctly
SD_APP_GB = 20
SD_LOG_GB = 10


def vault_run(command: str, stdin: bytes | None = None) -> str:
    """Run a shell command in the vault qube, returning its stdout"""
    result = subprocess.run(
        ["qvm-run", "--pass-io", "--no-gui", "vault", command],
        input=stdin,
        stdout=subprocess.PIPE,
        check=True,
    )
    return result.stdout.decode()


class FakeTailsDrive:
    """
    Stand-in for the Tails USB drives that "securedrop-manage --configure" reads from.
    """

    def __init__(self, submission_key: bytes) -> None:
        self.mountpoint: Path = manage.TAILS_PATH
        self.gnupg_path: Path = manage.TAILS_GNUPG_PATH
        self.submission_key = submission_key

    def insert_secure_viewing_station(self) -> None:
        """Plug in a drive whose GnuPG keyring holds the submission key"""
        self.eject()
        vault_run(f"sudo mkdir -p -- {self.gnupg_path}")
        vault_run(f"sudo chown -R user:user -- {self.mountpoint}")
        vault_run(f"chmod 700 -- {self.gnupg_path}")
        vault_run(f"gpg --homedir {self.gnupg_path} --batch --import", stdin=self.submission_key)

    def insert_journalist_workstation(self, ji_config_path: Path) -> None:
        """Plug in a drive holding the Journalist Interface details"""
        self.eject()
        vault_run(f"sudo mkdir -p -- {ji_config_path.parent}")
        vault_run(f"sudo chown -R user:user -- {self.mountpoint}")
        vault_run(f"cat > {ji_config_path}", stdin=FAKE_JI_CONFIG.encode())

    def eject(self) -> None:
        """Unplug whichever drive is currently plugged in, if any"""
        vault_run(f"gpgconf --homedir {self.gnupg_path} --kill all 2>/dev/null || true")
        vault_run(f"sudo rm -rf -- {self.mountpoint}")


@pytest.fixture
def tails_drive(proj_root: Path) -> Iterator[FakeTailsDrive]:
    # Never touch an actually-mounted Tails drive: ejecting deletes its contents
    mountpoint: Path = manage.TAILS_PATH
    if vault_run(f"test -e {mountpoint} && echo present || echo absent").strip() == "present":
        pytest.fail(f"{mountpoint} already exists in vault; refusing to overwrite it")

    drive = FakeTailsDrive((proj_root / "sd-journalist.sec").read_bytes())

    yield drive

    drive.eject()


@pytest.fixture
def ji_config_path(request: pytest.FixtureRequest) -> Path:
    """
    Where the Journalist Interface details live on the Workstation drive.

    Defaults to the location used since securedrop 2.13.0; parametrize the
    fixture indirectly to test the legacy (git) location instead.
    """
    attribute = getattr(request, "param", "TAILS_PKG_JOURNALIST_INTERFACE_CONFIG")
    path: Path = getattr(manage, attribute)
    return path


@pytest.fixture
def config_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect the dom0 config directory, so tests don't clobber the real one"""
    config_path = tmp_path / "securedrop-manage"
    config_path.mkdir()
    monkeypatch.setattr(manage, "CONFIG_PATH", config_path)
    return config_path


Answer = str | Callable[[], str]


@pytest.fixture
def answer_prompts(monkeypatch: pytest.MonkeyPatch) -> Callable[[list[Answer]], None]:
    """
    Fixture factory to answer the script's interactive prompts, in order.
    """

    def _answer_prompts(answers: list[Answer]) -> None:
        remaining = iter(answers)

        def fake_input(prompt: str = "") -> str:
            try:
                answer = next(remaining)
            except StopIteration:
                raise AssertionError(f"unexpected prompt: {prompt}")
            return answer() if callable(answer) else answer

        monkeypatch.setattr("builtins.input", fake_input)

    return _answer_prompts


def submission_key_fingerprint(key_file: Path) -> str:
    gpg_output = subprocess.check_output(
        ["gpg", "--show-keys", "--with-fingerprint", "--with-colon", key_file], text=True
    )
    fingerprints = manage.extract_secret_key_fingerprints(gpg_output)
    assert len(fingerprints) == 1
    return fingerprints[0]


@pytest.mark.parametrize(
    "ji_config_path",
    [
        pytest.param("TAILS_PKG_JOURNALIST_INTERFACE_CONFIG", id="package-location"),
        pytest.param("TAILS_GIT_JOURNALIST_INTERFACE_CONFIG", id="legacy-git-location"),
    ],
    indirect=True,
)
def test_import_config(
    tails_drive: FakeTailsDrive,
    ji_config_path: Path,
    config_path: Path,
    answer_prompts: Callable[[list[Answer]], None],
    proj_root: Path,
) -> None:
    tails_drive.insert_secure_viewing_station()

    def swap_in_workstation_drive() -> str:
        """This prompt asks for the other USB drive, so hand it the other drive"""
        tails_drive.insert_journalist_workstation(ji_config_path)
        return "y"

    answer_prompts(
        [
            "y",  # ready to import the submission key
            swap_in_workstation_drive,  # ready to import the Journalist Interface details
            "y",  # the imported Journalist Interface details are correct
            str(SD_APP_GB),
            str(SD_LOG_GB),
        ]
    )

    manage.import_config()

    # The submission key was fetched off the Secure Viewing Station drive
    imported_key = config_path / "sd-journalist.sec"
    assert imported_key.is_file()
    expected_fpr = submission_key_fingerprint(proj_root / "sd-journalist.sec")
    assert submission_key_fingerprint(imported_key) == expected_fpr

    # ...and the Journalist Interface details off the Workstation drive
    config = json.loads((config_path / "config.json").read_text())
    assert config == {
        "submission_key_fpr": expected_fpr,
        "hidserv": {
            "hostname": f"{FAKE_JI_ADDRESS}.onion",
            "key": FAKE_JI_AUTH_TOKEN,
        },
        "environment": "prod",
        "vmsizes": {"sd_app": SD_APP_GB, "sd_log": SD_LOG_GB},
    }

    manage.validate_config(config_path)


def test_import_config_keeps_existing_submission_key(
    tails_drive: FakeTailsDrive,
    ji_config_path: Path,
    config_path: Path,
    answer_prompts: Callable[[list[Answer]], None],
    proj_root: Path,
) -> None:
    """
    With the submission key already imported, only the Journalist Interface
    details are asked for, so only the Workstation drive is needed.
    """
    tails_drive.insert_journalist_workstation(ji_config_path)
    existing_key = config_path / "sd-journalist.sec"
    existing_key.write_bytes((proj_root / "sd-journalist.sec").read_bytes())

    answer_prompts(["y", "y", str(SD_APP_GB), str(SD_LOG_GB)])

    manage.import_config()

    assert existing_key.read_bytes() == (proj_root / "sd-journalist.sec").read_bytes()
    config = json.loads((config_path / "config.json").read_text())
    assert config["submission_key_fpr"] == submission_key_fingerprint(existing_key)
    assert config["hidserv"]["hostname"] == f"{FAKE_JI_ADDRESS}.onion"

    manage.validate_config(config_path)


def test_import_config_aborts_without_confirmation(
    tails_drive: FakeTailsDrive,
    config_path: Path,
    answer_prompts: Callable[[list[Answer]], None],
) -> None:
    """Answering "no" at the first prompt leaves the config directory untouched"""
    tails_drive.insert_secure_viewing_station()

    answer_prompts(["n"])

    manage.import_config()

    assert list(config_path.iterdir()) == []
