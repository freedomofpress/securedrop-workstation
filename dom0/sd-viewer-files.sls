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

sd-viewer-install-mimetype-handler-package:
  pkg.installed:
    - pkgs:
      - securedrop-workstation-svs-disp
      - evince
    - require:
      - sls: fpf-apt-test-repo

sd-viewer-install-libreoffice:
  pkg.installed:
    - name: libreoffice
    - retry:
        attempts: 3
        interval: 60
    - install_recommends: False
