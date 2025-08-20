import os
import subprocess
import tempfile
from datetime import datetime

import pytest
from qubesadmin import Qubes

# FEDORA_VERSION defined in conftest.py, and in future could be
# parameterized in this file
DEBIAN_DIST = "bookworm"


def _is_installed(pkg: str):
    """
    Check if package is installed.
    """
    try:
        subprocess.check_call(
            ["rpm", "-q", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        return True
    except subprocess.CalledProcessError:
        return False


# A bit clunky, but we have limited tooling options in dom0.
# TODO: Use sequoia when Qubes 4.3 is released
def _read_gpg_key_details(key_path: str):
    """# Use system-installed gpg to read pubkey details."""
    if not os.path.isfile(key_path):
        raise FileNotFoundError(f"No such file: {key_path}")

    with tempfile.TemporaryDirectory() as temp_home:
        subprocess.check_call(
            ["gpg2", "--homedir", temp_home, "--import", "--quiet", "--batch", "--yes", key_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        output = subprocess.check_output(
            ["gpg2", "--homedir", temp_home, "--with-colons", "--list-keys"]
        ).decode()

        return _parse_gpg_output(output)


def _parse_gpg_output(output: str):
    key_info = {"fingerprint": None, "uids": [], "expires": None}

    for line in output.splitlines():
        parts = line.strip().split(":")
        tag = parts[0]

        if tag == "fpr" and not key_info["fingerprint"]:
            key_info["fingerprint"] = parts[9]
        elif tag == "pub":
            exp = parts[6]
            if exp:
                key_info["expires"] = exp
        elif tag == "uid":
            key_info["uids"].append(parts[9])

    return key_info


def _validate_key(info: dict, expected_fpr: str, expected_uid: str, expected_expiry: str):
    """
    Check details of GPG key.
    """
    assert (
        info["fingerprint"] == expected_fpr
    ), f"Fingerprint mismatch: got {info['fingerprint']}, expected {expected_fpr}"

    assert len(info["uids"]) == 1, f"Expected 1 UID, found {len(info['uids'])}"

    assert (
        info["uids"][0] == expected_uid
    ), f"UID mismatch: got '{info['uids'][0]}', expected '{expected_uid}'"

    if expected_expiry == "-1":
        assert not info["expires"], "Expected no expiry, but key expires"
    else:
        assert info["expires"], "Expected expiry date, but key has none"
        exp_date = datetime.utcfromtimestamp(int(info["expires"]))
        max_exp = datetime.strptime(expected_expiry, "%Y")
        assert (
            exp_date.year <= max_exp.year
        ), f"Bad key expiry year: {exp_date.date().year} > {max_exp.date().year}"


def _read_and_validate_key(keyfile_path: str, fpr: str, uid: str, expiry: str):
    info = _read_gpg_key_details(keyfile_path)
    _validate_key(info, fpr, uid, expiry)


def _parse_key_from_sources(sources):
    key_lines = []
    capturing = False

    for line in sources.splitlines():
        if capturing:
            # First line after header should be without "."
            if line.strip() == ".":
                key_lines.append(" ")
            else:
                key_lines.append(line.strip())
            if "END PGP PUBLIC KEY BLOCK" in line:
                break
        elif line.strip() == "Signed-By:":
            capturing = True  # Start capturing from the next line

    if not key_lines or "END PGP PUBLIC KEY BLOCK" not in key_lines[-1]:
        raise ValueError("No complete PGP key found")

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".asc", mode="w", encoding="utf-8"
    ) as tmp_file:
        tmp_file.write("\n".join(key_lines) + "\n")

    return tmp_file.name


def test_dom0_has_keyring_package(env):
    assert _is_installed("securedrop-workstation-keyring")

    if env == "dev":
        assert _is_installed("securedrop-workstation-keyring-dev")
    elif env == "staging":
        assert _is_installed("securedrop-workstation-keyring-staging")


def test_rpm_repo_config(config):
    repo = config["repo_file_name"]
    baseurl = config["yum_repo_url"]
    repo_file = f"/etc/yum.repos.d/{repo}"
    wanted_lines = [
        "[securedrop-workstation-dom0]",
        "gpgcheck=1",
        "skip_if_unavailable=False",
        "gpgkey=file://{}".format(config.get("signing_key")),
        "enabled=1",
        f"baseurl={baseurl}",
        "name=SecureDrop Workstation Qubes dom0 repo",
    ]
    with open(repo_file) as f:
        found_lines = [x.strip() for x in f.readlines()]

    assert found_lines == wanted_lines


def test_key_dom0(config):
    """Check the key in /etc/pki/rpm-gpg/, used for dom0 updates."""
    _read_and_validate_key(
        config["signing_key"],
        config["signing_key_fpr"],
        config["signing_key_uid"],
        config["signing_key_exp"],
    )


@pytest.mark.parametrize("template", ["small", "large"])
def test_key_apt_sources(config, template):
    """Check the key in the apt_sources file used for provisioning Debian-based templates."""
    app = Qubes()
    vm = app.domains[f"sd-{template}-{DEBIAN_DIST}-template"]
    apt_sources_filename = config["apt_sources"]
    stdout, _ = vm.run(f"cat {apt_sources_filename}")
    sources = stdout.decode()

    tmp_keyfile = _parse_key_from_sources(sources)

    _read_and_validate_key(
        tmp_keyfile,
        config["signing_key_fpr"],
        config["signing_key_uid"],
        config["signing_key_exp"],
    )
