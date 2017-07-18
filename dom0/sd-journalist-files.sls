# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-journalist-files
# ========
#
# Moves files in to place
#
##

/usr/local/bin/move-to-svs:
  require:
    - sls: sd-journalist
  file.managed:
    - source: salt://sd/sd-journalist/move-to-svs
    - user: root
    - group: root
    - mode: 755
