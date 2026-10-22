# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Launches the updater (via sdw-login) when the dom0 user logs in.
##

{% set gui_user = salt['cmd.shell']('groupmems -l -g qubes') %}

dom0-login-autostart-directory:
  file.directory:
    - name: /home/{{ gui_user }}/.config/autostart
    - user: {{ gui_user }}
    - group: {{ gui_user }}
    - mode: 700
    - makedirs: True

dom0-login-autostart-desktop-file:
  file.managed:
    - name: /home/{{ gui_user }}/.config/autostart/press.freedom.SecureDropUpdater.desktop
    - source: "salt://securedrop_shared/dom0-xfce-desktop-file.j2"
    - template: jinja
    - context:
        desktop_name: SDWLogin
        desktop_comment: Updates SecureDrop Workstation DispVMs at login
        desktop_exec: /usr/bin/sdw-login
    - user: {{ gui_user }}
    - group: {{ gui_user }}
    - mode: 664
    - require:
      - file: dom0-login-autostart-directory
