# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-journalist-files
# ========
#
# Moves files in to place
#
##

mkfifo /home/user/sdfifo:
  cmd.run

chmod 666 /home/user/sdfifo:
  cmd.run

/home/user/.config/mimeapps.list:
  file.managed:
    - source: salt://sd/sd-journalist/mimeapps.list
    - user: user
    - group: user
    - mode: 644
    - makedirs: True
