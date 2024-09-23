# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
include:
  - securedrop_salt.fpf-apt-repo

# install recommended Qubes VM packages for core functionality.
# Note: additional system packages are installed as dependencies
# of securedrop-workstation-config.
# See https://github.com/freedomofpress/securedrop-client/blob/main/debian/control
install-qubes-vm-recommended:
  pkg.installed:
    - pkgs:
      - qubes-vm-recommended

# install workstation-config and grsec kernel
sd-base-template-install-securedrop-packages:
  pkg.installed:
    - pkgs:
      - securedrop-qubesdb-tools
      - securedrop-workstation-config
      - securedrop-workstation-grsec
    - require:
      - sls: securedrop_salt.fpf-apt-repo

# Ensure that paxctld starts immediately. For AppVMs,
# use qvm.features.enabled = ["paxctld"] to ensure service start.
sd-workstation-template-enable-paxctld:
  service.running:
    - name: paxctld
    - enable: True
    - reload: True
    - require:
      - pkg: sd-base-template-install-securedrop-packages