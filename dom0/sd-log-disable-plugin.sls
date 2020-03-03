# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Disable securedrop-log rsyslog plugin in sd-log vm
##


sd-log-remove-rsyslog-qubes-plugin:
  file.blockreplace:
    - name: /rw/config/rc.local
    - append_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        # Add sd-rsyslog.conf file for syslog
        rm -f /etc/rsyslog.d/sdlog.conf
        systemctl restart rsyslog
  cmd.run:
    - name: rm -f /etc/rsyslog.d/sdlog.conf && systemctl restart rsyslog
