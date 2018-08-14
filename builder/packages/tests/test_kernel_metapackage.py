import os

KERNEL_VERSION = "4.14.53"

DEB_FILE = "securedrop-workstation-grsec_{}-1_amd64.deb".format(KERNEL_VERSION)


def test_hosts_file(host):
    f = host.file(DEB_FILE)
    assert f.exists
