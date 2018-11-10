# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-proxy-files
# ========
#
# Moves files in to place
#
##

sd-proxy-create-feedback-pipe:
  file.mknod:
    - name: /home/user/sdfifo
    - ntype: p
    - user: user
    - group: user
    - mode: 666
  require:
    - cmd: sd-proxy-install-python-futures

/home/user/.config/mimeapps.list:
  file.managed:
    - source: salt://sd/sd-proxy/mimeapps.list
    - user: user
    - group: user
    - mode: 644
    - makedirs: True
  require:
    - cmd: sd-proxy-install-python-futures

sd-proxy-install-python-qt4:
  pkg.installed:
    - pkgs:
        - python-qt4
  require:
    - cmd: sd-proxy-install-python-futures
