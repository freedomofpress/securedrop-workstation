# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-viewer-files
# ========
#
# Installs configuration packages specific to the Viewer DispVM,
# used for opening submissions.
#
##

include:
  - securedrop_salt.fpf-apt-repo
  - securedrop_salt.sd-logging-setup

sd-viewer-install-metapackage:
  pkg.installed:
    - pkgs:
      - securedrop-workstation-viewer
    - require:
      - sls: securedrop_salt.fpf-apt-repo
