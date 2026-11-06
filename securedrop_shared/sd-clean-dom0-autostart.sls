# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Removes the login autostart and updater state shared by all products. Only
# apply this when the last product is being uninstalled.
##

{% set gui_user = salt['cmd.shell']('groupmems -l -g qubes') %}

remove-dom0-shared-config-files:
  file.absent:
    - names:
      - /home/{{ gui_user }}/.config/autostart/press.freedom.SecureDropUpdater.desktop
      - /home/{{ gui_user }}/.securedrop_updater
