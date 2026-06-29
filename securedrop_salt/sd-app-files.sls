# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-app-files
# ========
#
# Moves files into place on sd-inbox-debian-$sdvars.debian_version
#
##
include:
  - securedrop_salt.fpf-apt-repo
  - securedrop_salt.sd-logging-setup

# FPF repo is setup in base template, and then cloned as
# "sd-inbox-debian-$sdvars.debian_version"
install-securedrop-app-package:
  pkg.installed:
    - pkgs:
      - securedrop-app
    - require:
      - sls: securedrop_salt.fpf-apt-repo
