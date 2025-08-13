import socket
from datetime import UTC, datetime, timedelta
from pathlib import Path

if socket.gethostname() != "dom0":
    import pysequoia
    from debian import deb822

from conftest import skip_in_dom0

# A couple of tests are skipped in dom0 since:
#  - they rely on poetry-installed dependencies (not trival to get in dom0)
#  - This test may go away later once the .sources files in the keyring package

ROOT = Path(__name__).parent.parent


@skip_in_dom0
def test_apt_sources():
    """Verify the key in the sources file is our prod signing key"""
    path = ROOT / "securedrop_salt/apt_freedom_press.sources.j2"

    sources = deb822.Sources(path.read_text())
    assert_key(sources["Signed-By"].encode())


@skip_in_dom0
def test_dom0_key():
    path = ROOT / "securedrop_salt/securedrop-release-signing-pubkey-2021.asc"
    assert_key(path.read_bytes())


def assert_key(cert_bytes: bytes):
    """verify there is only one key, our release key, and that it has the right expiry"""
    key = pysequoia.Cert.from_bytes(cert_bytes)

    assert key.fingerprint.upper() == "2359E6538C0613E652955E6C188EDD3B7B22E6A3"
    assert len(key.user_ids) == 1
    assert (
        str(key.user_ids[0])
        == "SecureDrop Release Signing Key <securedrop-release-key-2021@freedom.press>"
    )
    assert key.expiration.year == 2027
    # Fail if we are within 6 months of the key's expiry
    assert datetime.now(tz=UTC) < (
        key.expiration - timedelta(days=6 * 30)
    ), "key expires in less than 6 months"
