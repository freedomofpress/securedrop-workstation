# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-small-template-files
# ========
#
# Installs packages on small template (used by sd-app, sd-gpg, sd-log, sd-proxy)
#
##
include:
  - fpf-apt-test-repo
  - sd-logging-setup

# FPF repo is setup in "securedrop-workstation" template
install-small-template-securedrop-packages:
  pkg.installed:
    - pkgs:
      - securedrop-client
      - securedrop-proxy
    - require:
      - sls: fpf-apt-test-repo
