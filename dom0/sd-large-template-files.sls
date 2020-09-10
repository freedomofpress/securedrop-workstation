# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-large-template-files
# ========
#
# Installs packages on large template (used by sd-devices, sd-viewer)
#
##
include:
  - fpf-apt-test-repo
  - sd-logging-setup

# FPF repo is setup in "securedrop-workstation" template
install-large-template-securedrop-packages:
  pkg.installed:
    - pkgs:
      - securedrop-workstation-svs-disp
      - evince
      - securedrop-export
    - require:
      - sls: fpf-apt-test-repo

install-libreoffice:
  pkg.installed:
    - name: libreoffice
    - retry:
        attempts: 3
        interval: 60
    - install_recommends: False
