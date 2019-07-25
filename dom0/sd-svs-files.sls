# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-svs-files
# ========
#
# Moves files into place on sd-svs-template
#
##
include:
  - fpf-apt-test-repo

# FPF repo is setup in "securedrop-workstation" template
install-securedrop-client-package:
  pkg.installed:
    - pkgs:
      - securedrop-client
    - require:
      - sls: fpf-apt-test-repo
