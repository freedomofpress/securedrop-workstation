# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-app-files
# ========
#
# Moves files into place on sd-app-template
#
##
include:
  - fpf-apt-test-repo
  - sd-logging-setup

# FPF repo is setup in "securedrop-workstation" template
install-securedrop-client-package:
  pkg.installed:
    - pkgs:
      - securedrop-client
    - require:
      - sls: fpf-apt-test-repo
