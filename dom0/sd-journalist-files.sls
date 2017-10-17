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
  file.managed:
    - source: salt://sd/sd-journalist/move-to-svs
    - user: root
    - group: root
    - mode: 755

/usr/local/bin/sd-process-download:
  file.managed:
    - source: salt://sd/sd-journalist/sd-process-download
    - user: root
    - group: root
    - mode: 755

/usr/local/bin/do-not-open:
  file.managed:
    - source: salt://sd/sd-journalist/do-not-open
    - user: root
    - group: root
    - mode: 755

/usr/local/bin/sd-process-feedback:
  file.managed:
    - source: salt://sd/sd-journalist/sd-process-feedback
    - user: root
    - group: root
    - mode: 755

/usr/local/bin/mm.py:
  file.managed:
    - source: salt://sd/sd-journalist/mm.py
    - user: root
    - group: root
    - mode: 755

/usr/local/bin/pipereader.py:
  file.managed:
    - source: salt://sd/sd-journalist/pipereader.py
    - user: root
    - group: root
    - mode: 755

/etc/qubes-rpc/sd-process.Feedback:
  file.managed:
    - source: salt://sd/sd-journalist/sd-process.Feedback
    - user: root
    - group: root
    - mode: 755

/usr/local/share/applications/sd-process-download.desktop:
  file.managed:
    - source: salt://sd/sd-journalist/sd-process-download.desktop
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/usr/local/share/applications/do-not-open.desktop:
  file.managed:
    - source: salt://sd/sd-journalist/do-not-open.desktop
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/home/user/.config/mimeapps.list:
  file.managed:
    - source: salt://sd/sd-journalist/mimeapps.list
    - user: user
    - group: user
    - mode: 644
    - makedirs: True

sudo update-desktop-database /usr/local/share/applications:
  cmd.run
