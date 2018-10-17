# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-svs-disp-files
# ========
#
# Moves files into place on sd-svs-disp
#
##

sd-svs-disp-write-mimetyeps:
  file.managed:
    - name: /usr/share/applications/mimeapps.list
    - source: salt://sd/sd-svs/mimeapps-sd-svs-disp.list
    - user: root
    - group: root
    - mode: 644

sudo update-mime-database /usr/share/mime:
  cmd.run
