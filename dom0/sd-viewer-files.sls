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
  - fpf-apt-test-repo
  - sd-logging-setup

sd-viewer-install-metapackage:
  pkg.installed:
    - pkgs:
      - securedrop-workstation-viewer
    - require:
      - sls: fpf-apt-test-repo

sd-viewer-install-libreoffice:
  pkg.installed:
    - name: libreoffice
    - retry:
        attempts: 3
        interval: 60
    - install_recommends: False
