# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

include:
  - securedrop_salt.fpf-apt-repo

install-securedrop-gpg-package:
  pkg.installed:
    - pkgs:
      - securedrop-gpg-config
    - require:
      - sls: securedrop_salt.fpf-apt-repo
