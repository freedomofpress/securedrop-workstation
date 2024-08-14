# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-devices-files
# ========
#
# Moves files into place on sd-devices
#
##
include:
  - securedrop_salt.fpf-apt-repo
  - securedrop_salt.sd-logging-setup

# Install securedrop-export package https://github.com/freedomofpress/securedrop-export
sd-devices-install-package:
  pkg.installed:
    - name: securedrop-export
    - require:
      - sls: securedrop_salt.fpf-apt-repo
