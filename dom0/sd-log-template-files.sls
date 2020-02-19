# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
include:
  - fpf-apt-test-repo

sd-log-install-securedrop-log-package:
  pkg.installed:
    - pkgs:
      - redis-server
      - redis
      - securedrop-log
    - require:
      - sls: fpf-apt-test-repo

redis:
  service.running:
    - enable: True

securedrop-log:
  service.running:
    - enable: True
