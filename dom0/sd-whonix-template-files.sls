# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-whonix-template-files
# ========
#
# Installs configuration packages specific to the sd-whonix
# used for network calls.
#
##

include:
  - fpf-apt-test-repo

sd-whonix-install-logging:
  pkg.installed:
    - pkgs:
      - securedrop-log
    - require:
      - sls: fpf-apt-test-repo

