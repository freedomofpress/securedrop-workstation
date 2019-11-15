# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
include:
  - fpf-apt-test-repo

install-securedrop-log-package:
  pkg.installed:
    - pkgs:
      - securedrop-log
    - require:
      - sls: fpf-apt-test-repo
