from tests import dom0_stubs

# Must happen before anything imports qubesadmin, dnf or systemd
dom0_stubs.install()
