# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# removes securedrop-log rsyslog plugin in whonix-gw-15
##

remove-securedrop-log-package-from-whonix:
  pkg.removed:
    - pkgs:
      - securedrop-log