# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

include:
  - fpf-apt-test-repo

sd-workstation-template-install-kernel-config-packages:
  pkg.installed:
    - pkgs:
      - securedrop-workstation-config
      - securedrop-workstation-grsec
    - require:
      - sls: fpf-apt-test-repo
      - qvm: sd-workstation-template
