# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-journalist-files
# ========
#
# Moves files in to place
#
##

sd-journalist-create-feedback-pipe:
  file.mknod:
    - name: /home/user/sdfifo
    - ntype: p
    - user: user
    - group: user
    - mode: 666
  require:
    - cmd: sd-journalist-install-python-futures

/home/user/.config/mimeapps.list:
  file.managed:
    - source: salt://sd/sd-journalist/mimeapps.list
    - user: user
    - group: user
    - mode: 644
    - makedirs: True
  require:
    - cmd: sd-journalist-install-python-futures

sd-journalist-install-python-qt4:
  pkg.installed:
    - pkgs:
        - python-qt4
  require:
    - cmd: sd-journalist-install-python-futures
