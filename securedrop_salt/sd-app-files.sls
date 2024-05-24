# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-app-files
# ========
#
# Moves files into place on sd-small-$sdvars.distribution-template
#
##
include:
  - securedrop_salt.fpf-apt-repo
  - securedrop_salt.sd-logging-setup

# FPF repo is setup in "securedrop-workstation-$sdvars.distribution" template,
# and then cloned as "sd-small-$sdvars.distribution-template"
install-securedrop-client-package:
  pkg.installed:
    - pkgs:
      - securedrop-client
    - require:
      - sls: securedrop_salt.fpf-apt-repo
