# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
##
# Updates to systemd configuration in dom0
##

# Identify the GUI user by group membership
{% set gui_user = salt['cmd.shell']('groupmems -l -g qubes') %}
{% set gui_user_id = salt['cmd.shell']('id -u ' + gui_user) %}

enable-user-units:
  cmd.run:
    - name: |
        systemctl --user daemon-reload
        systemctl --user enable sdw-notify.timer
    - runas: {{ gui_user }}
    - env:
      # Even with "runas", "systemctl --user" from root will fail unless we
      # tell it explicitly how to connect to the user systemd.
      - XDG_RUNTIME_DIR: /run/user/{{ gui_user_id }}
