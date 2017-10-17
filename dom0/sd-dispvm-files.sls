# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-dispvm-files
# ========
#
# Moves files into place on sd-dispvm
#
##

/usr/local/bin/decrypt-sd-submission:
  file.managed:
    - source: salt://sd/decrypt/decrypt-sd-submission
    - user: root
    - group: root
    - mode: 755

/usr/local/share/mime/packages/application-x-sd-xfer.xml:
  file.managed:
    - source: salt://sd/decrypt/application-x-sd-xfer.xml
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/usr/local/share/applications/decrypt-sd-submission.desktop:
  file.managed:
    - source: salt://sd/decrypt/decrypt-sd-submission.desktop
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

# /etc/profile.d/qubes-gpg.sh:
/home/user/.profile:
  file.managed:
    - source: salt://sd/decrypt/dot-profile
    - user: root
    - group: root
    - mode: 755

sudo update-mime-database /usr/local/share/mime:
  cmd.run

sudo update-desktop-database /usr/local/share/applications:
  cmd.run
