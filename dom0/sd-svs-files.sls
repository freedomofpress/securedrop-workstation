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

sd-svs-qubes-gpg-domain-profile-settings:
  file.managed:
    - name: /etc/profile.d/sd-svs-qubes-gpg-domain.sh
    - source: salt://sd/sd-svs/dot-profile
    - user: root
    - group: root
    - mode: 644
    - require:
      - qvm: sd-svs-template

sd-svs-open-in-dvm-desktop-file:
  file.managed:
    - name: /usr/share/applications/open-in-dvm.desktop
    - source: salt://sd/sd-svs/open-in-dvm.desktop
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - require:
      - qvm: sd-svs-template

sd-svs-custom-mimeapps-list:
  file.managed:
    - name: /usr/share/applications/mimeapps.list
    - source: salt://sd/sd-svs/mimeapps.list
    - user: user
    - group: user
    - mode: 644
    - makedirs: True
    - require:
      - qvm: sd-svs-template

sd-svs-update-mime-database:
  cmd.run:
    - name: sudo update-mime-database /usr/share/mime
    - require:
      - file: sd-svs-custom-mimeapps-list

sd-svs-update-desktop-database:
  cmd.run:
    - name: sudo update-desktop-database /usr/share/applications
    - require:
      - file: sd-svs-custom-mimeapps-list

# FPF repo is setup in "securedrop-workstation" template
install-securedrop-client-package:
  pkg.installed:
    - pkgs:
      - python3-pyqt5
      - python3-pyqt5.qtsvg
      - securedrop-client
    - require:
      - sls: fpf-apt-test-repo
      - qvm: sd-svs-template
