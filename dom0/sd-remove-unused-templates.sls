# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

run-remove-upgrade-scripts:
  cmd.script:
    - name: salt://handle-upgrade
    - args: remove
