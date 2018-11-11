# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-gpg-files
# ========
#
# Does hots config for sd-gpg split gpg AppVM
#
##

/home/user/.profile:
  file.append:
    - text: "export QUBES_GPG_AUTOACCEPT=28800"

/tmp/sd-journalist.sec:
  file.managed:
    - source: salt://sd/sd-journalist.sec
    - user: user
    - group: user
    - mode: 644

sudo -u user gpg --import /tmp/sd-journalist.sec:
  cmd.run
