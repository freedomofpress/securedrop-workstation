# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-export-files
# ========
#
# Moves files into place on sd-export
#
##
include:
  - fpf-apt-test-repo

# Libreoffice needs to be installed here to convert to pdf to allow printing
sd-export-install-libreoffice:
  pkg.installed:
    - name: libreoffice
    - retry:
        attempts: 3
        interval: 60
    - install_recommends: False

# Install securedrop-export package https://github.com/freedomofpress/securedrop-export
sd-export-install-package:
  pkg.installed:
    - name: securedrop-export
