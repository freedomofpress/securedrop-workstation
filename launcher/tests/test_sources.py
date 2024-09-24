"""
Test apt sources files

Strictly speaking this doesn't have to do with the launcher, but
it needs dependencies installed and to be run under pytest
"""

from pathlib import Path

import pysequoia
from debian import deb822

SECUREDROP_SALT = Path(__file__).parent.parent.parent / "securedrop_salt"


def test_prod_sources():
    """Verify the key in the aptsources file is our prod signing key"""
    path = SECUREDROP_SALT / "apt_freedom_press.sources.j2"

    sources = deb822.Sources(path.read_text())
    key = pysequoia.Cert.from_bytes(sources["Signed-By"].encode())
    assert key.fingerprint.upper() == "2359E6538C0613E652955E6C188EDD3B7B22E6A3"
    assert len(key.user_ids) == 1
    assert (
        str(key.user_ids[0])
        == "SecureDrop Release Signing Key <securedrop-release-key-2021@freedom.press>"
    )
    assert key.expiration.year == 2027


def test_test_sources():
    """Verify the key in the apt-test sources file is our dev signing key"""
    path = SECUREDROP_SALT / "apt-test_freedom_press.sources.j2"

    sources = deb822.Sources(path.read_text())
    key = pysequoia.Cert.from_bytes(sources["Signed-By"].encode())
    assert key.fingerprint.upper() == "83127F68BABB04F3FE9A69AA545E94503FAB65AB"
    assert len(key.user_ids) == 1
    assert str(key.user_ids[0]) == "SecureDrop TESTING key <securedrop@freedom.press>"
    assert key.expiration is None
