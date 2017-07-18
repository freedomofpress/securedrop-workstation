# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-svs-files
# ========
#
# Moves files into place on sd-svs
#
##

/usr/local/bin/accept-sd-xfer-extracted:
  require:
    - sls: sd-svs
  file.managed:
    - source: salt://sd/sd-svs/accept-sd-xfer-extracted
    - user: root
    - group: root
    - mode: 755

/usr/share/mime/packages/application-x-sd-xfer-extracted.xml:
  require:
    - sls: sd-svs
  file.managed:
    - source: salt://sd/sd-svs/application-x-sd-xfer-extracted.xml
    - user: root
    - group: root
    - mode: 644

/usr/share/applications/accept-sd-xfer-extracted.desktop:
  require:
    - sls: sd-svs
  file.managed:
    - source: salt://sd/sd-svs/accept-sd-xfer-extracted.desktop
    - user: root
    - group: root
    - mode: 644

/usr/share/applications/open-in-dvm.desktop:
  require:
    - sls: sd-svs
  file.managed:
    - source: salt://sd/sd-svs/open-in-dvm.desktop
    - user: root
    - group: root
    - mode: 644

/home/user/.config/mimeapps.list:
  require:
    - sls: sd-svs
  file.managed:
    - source: salt://sd/sd-svs/mimeapps.list
    - user: user
    - group: user
    - mode: 644
    - makedirs: True
