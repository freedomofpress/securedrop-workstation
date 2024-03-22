# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
include:
  - fpf-apt-repo

# TODO: test if this works, if not it may need to be a qvm-run command
sd-base-template-install-additional-packages:
  pkg.installed:
    - pkgs:
      - qubes-core-agent-passwordless-root
      - rsyslog
      - mailcap
      - apparmor
      - apparmor-utils

sd-base-template-install-securedrop-packages:
  pkg.installed:
    - pkgs:
      - securedrop-workstation-config
      - securedrop-workstation-grsec
    - require:
      - sls: fpf-apt-repo
