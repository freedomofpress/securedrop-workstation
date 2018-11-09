# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-gpg-files
# ========
#
# Does hots config for sd-gpg split gpg AppVM
#
##

sd-gpg-copy-submission-private-key:
  file.managed:
    - name: /tmp/sd-journalist.sec
    - source: salt://sd/sd-journalist.sec
    - user: user
    - group: user
    - mode: 644
    - require:
      - qvm: sd-gpg

sd-gpg-import-submission-private-key:
  cmd.run:
    - name: sudo -u user gpg --import /tmp/sd-journalist.sec
    - require:
      - file: sd-gpg-copy-submission-private-key
