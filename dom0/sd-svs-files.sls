# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-svs-files
# ========
#
# Moves files into place on sd-svs
#
##
include:
  - fpf-apt-test-repo

sd-svs-configure-gpg-domain:
  file.managed:
    - name: /etc/profile.d/sd-svs-qubes-gpg-domain.sh
    - source: salt://sd/sd-svs/dot-profile
    - user: root
    - group: root
    - mode: 644

sd-svs-open-in-dvm-desktop-file:
  file.managed:
    - name: /usr/share/applications/open-in-dvm.desktop
    - source: salt://sd/sd-svs/open-in-dvm.desktop
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

sd-svs-configure-mimetypes:
  file.managed:
    - name: /usr/share/applications/mimeapps.list
    - source: salt://sd/sd-svs/mimeapps.list
    - user: user
    - group: user
    - mode: 644
    - makedirs: True
  cmd.run:
    - name: sudo update-desktop-database /usr/share/applications
    - require:
      - file: sd-svs-configure-mimetypes

# FPF repo is setup in "securedrop-workstation" template
install-securedrop-client-package:
  pkg.installed:
    - pkgs:
      - python3-pyqt5
      - python3-pyqt5.qtsvg
      - securedrop-client
    - require:
      - sls: fpf-apt-test-repo
