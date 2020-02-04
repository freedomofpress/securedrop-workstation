# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
##
# Update /etc/crontab with any cron jobs we need to run regularly
##

# Identify the GUI user by group membership
{% set gui_user = salt['cmd.shell']('groupmems -l -g qubes') %}

# Add an hourly job, run as the GUI user, to display a warning if the
# SecureDrop preflight updater has not run for longer than a defined
# warning threshold.
dom0-crontab-update-notify:
  file.blockreplace:
    - name: /etc/crontab
    - append_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        0 * * * * {{gui_user}} DISPLAY=:0 /usr/bin/securedrop-update-notify
