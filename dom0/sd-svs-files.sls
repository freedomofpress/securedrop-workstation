# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-svs-files
# ========
#
# Moves files into place on sd-svs
#
##

/etc/profile.d/sd-svs-qubes-gpg-domain.sh:
  file.managed:
    - source: salt://sd/sd-svs/dot-profile
    - user: root
    - group: root
    - mode: 644

/usr/share/applications/open-in-dvm.desktop:
  file.managed:
    - source: salt://sd/sd-svs/open-in-dvm.desktop
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/usr/share/applications/mimeapps.list:
  file.managed:
    - source: salt://sd/sd-svs/mimeapps.list
    - user: user
    - group: user
    - mode: 644
    - makedirs: True

sudo update-mime-database /usr/share/mime:
  cmd.run

sudo update-desktop-database /usr/share/applications:
  cmd.run

# FPF repo is setup in "securedrop-workstation" template
install-securedrop-client-package:
  pkg.installed:
    - pkgs:
      - python3-pyqt5
      - python3-pyqt5.svg
      - securedrop-client
  require:
    - sls: fpf-apt-test-repo
