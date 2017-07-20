# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-dispvm-files
# ========
#
# Moves files into place on sd-dispvm
#
##

/usr/bin/decrypt-sd-submission:
  file.managed:
    - source: salt://sd/decrypt/decrypt-sd-submission
    - user: root
    - group: root
    - mode: 755

/usr/share/mime/packages/application-x-sd-xfer.xml:
  file.managed:
    - source: salt://sd/decrypt/application-x-sd-xfer.xml
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/usr/share/applications/decrypt-sd-submission.desktop:
  file.managed:
    - source: salt://sd/decrypt/decrypt-sd-submission.desktop
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/tmp/sd-journalist.sec:
  file.managed:
    - source: salt://sd/sd-journalist.sec
    - user: user
    - group: user
    - mode: 644

sudo update-mime-database /usr/share/mime:
  cmd.run

sudo update-desktop-database /usr/share/applications:
  cmd.run

sudo -u user gpg --import /tmp/sd-journalist.sec:
  cmd.run

touch /home/user/.qubes-dispvm-customized:
  cmd.run
