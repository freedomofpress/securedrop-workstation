# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
include:
  - securedrop_salt.fpf-apt-repo
  - securedrop_salt.sd-logging-setup

# Depends on FPF-controlled apt repo
install-securedrop-proxy-package:
  pkg.installed:
    - pkgs:
      - securedrop-proxy
    - require:
      - sls: securedrop_salt.fpf-apt-repo
