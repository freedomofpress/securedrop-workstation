# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
include:
  - fpf-apt-repo

# install recommended Qubes VM packages for core functionality
install-qubes-vm-recommended:
  pkg.installed:
    - pkgs:
      - qubes-vm-recommended

# install additional base packages required by SecureDrop
sd-base-template-install-additional-packages:
  pkg.installed:
    - pkgs:
      - rsyslog
      - mailcap
      - apparmor

# install workstation-config and grsec kernel
sd-base-template-install-securedrop-packages:
  pkg.installed:
    - pkgs:
      - securedrop-qubesdb
      - securedrop-workstation-config
      - securedrop-workstation-grsec
    - require:
      - sls: fpf-apt-repo
