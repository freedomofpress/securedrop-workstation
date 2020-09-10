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

sd-viewer-install-mimetype-handler-package:
  pkg.installed:
    - pkgs:
      - evince

# TEMPORARY: local package build for debugging
sd-viewer-install-mimetype-handler-package-local:
  file.managed:
    - name: /opt/securedrop-workstation-svs-disp.deb
    - source: salt://sd/sd-workstation/securedrop-workstation-svs-disp_0.2.2+buster_all.deb
    - mode: 644
  cmd.run:
   - name: apt install -y /opt/securedrop-workstation-svs-disp.deb

sd-viewer-install-libreoffice:
  pkg.installed:
    - name: libreoffice
    - retry:
        attempts: 3
        interval: 60
    - install_recommends: False
