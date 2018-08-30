import pytest

KERNEL_VERSION = "4.14.58"
PACKAGE_NAME = "securedrop-workstation-grsec"
PACKAGE_VERSION = "{}-1".format(KERNEL_VERSION)
PACKAGE_ARCH = "amd64"
DEB_FILE = "{}_{}_{}.deb".format(PACKAGE_NAME, PACKAGE_VERSION, PACKAGE_ARCH)
KERNEL_DEPENDS = "linux-image-{}-grsec, linux-headers-{}-grsec, libelf-dev, paxctld".format(KERNEL_VERSION, KERNEL_VERSION)  # noqa: E501
MAINTAINER = "SecureDrop Team <securedrop@freedom.press>"


def test_hosts_file(host):
    f = host.file(DEB_FILE)
    assert f.exists


@pytest.mark.parametrize("field,value", [
    ("Version", PACKAGE_VERSION),
    ("Depends", KERNEL_DEPENDS),
    ("Maintainer", MAINTAINER),
    ("Package", PACKAGE_NAME),
    ("Architecture", PACKAGE_ARCH),
])
def test_control_fields(host, field, value):
    c = "dpkg-deb -f securedrop-workstation-grsec_{}_amd64.deb {}".format(PACKAGE_VERSION, field)  # noqa: E501
    assert host.check_output(c) == value


def test_lintian(host):
    cmd = host.run("lintian {}".format(DEB_FILE))
    assert cmd.rc == 0
