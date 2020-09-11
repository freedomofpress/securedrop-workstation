# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
include:
  - fpf-apt-test-repo
  - sd-logging-setup

# Depends on FPF-controlled apt repo, already present
# in underlying "securedrop-workstation" base template.
install-securedrop-proxy-package:
  pkg.installed:
    - pkgs:
      - securedrop-proxy
    - require:
      - sls: fpf-apt-test-repo

# Remove the legacy config file location
remove-legacy-sd-proxy-config:
  file.absent:
    - names:
      - /etc/sd-proxy.yaml
