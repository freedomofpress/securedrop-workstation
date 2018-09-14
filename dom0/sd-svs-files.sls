# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-svs-files
# ========
#
# Moves files into place on sd-svs
#
##

/usr/local/bin/decrypt-sd-submission:
  file.managed:
    - source: salt://sd/sd-svs/decrypt-sd-submission
    - user: root
    - group: root
    - mode: 755

/home/user/.profile:
  file.managed:
    - source: salt://sd/sd-svs/dot-profile
    - user: root
    - group: root
    - mode: 755

/usr/local/bin/accept-sd-xfer-extracted:
  file.managed:
    - source: salt://sd/sd-svs/accept-sd-xfer-extracted
    - user: root
    - group: root
    - mode: 755

/usr/local/share/mime/packages/application-x-sd-xfer.xml:
  file.managed:
    - source: salt://sd/sd-svs/application-x-sd-xfer.xml
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/usr/local/share/applications/decrypt-sd-submission.desktop:
  file.managed:
    - source: salt://sd/sd-svs/decrypt-sd-submission.desktop
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/usr/local/share/applications/open-in-dvm.desktop:
  file.managed:
    - source: salt://sd/sd-svs/open-in-dvm.desktop
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/home/user/.config/mimeapps.list:
  file.managed:
    - source: salt://sd/sd-svs/mimeapps.list
    - user: user
    - group: user
    - mode: 644
    - makedirs: True

sudo update-mime-database /usr/local/share/mime:
  cmd.run

sudo update-desktop-database /usr/local/share/applications:
  cmd.run

/home/user/Sources:
  file.directory:
    - user: user
    - group: user
    - dir_mode: 755
    - file_mode: 644
