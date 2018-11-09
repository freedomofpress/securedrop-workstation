# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-svs-disp-files
# ========
#
# Moves files into place on sd-svs-disp
#
##
include:
  - fpf-apt-test-repo

sd-svs-disp-install-mimetype-handler-package:
  pkg.installed:
    - pkgs:
      - securedrop-workstation-svs-disp
    - require:
      - sls: fpf-apt-test-repo
