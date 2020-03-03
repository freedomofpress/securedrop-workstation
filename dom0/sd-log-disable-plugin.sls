# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Disable securedrop-log rsyslog plugin in sd-log vm
# Fixes https://github.com/freedomofpress/securedrop-log/issues/15
# Due to a single Debian package for both logging and also sd-log vm
# we need to do the following step.
##


sd-log-remove-rsyslog-qubes-plugin:
  file.blockreplace:
    - name: /rw/config/rc.local
    - append_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        # Removes sdlog.conf file for rsyslog
        rm -f /etc/rsyslog.d/sdlog.conf
        systemctl restart rsyslog
  cmd.run:
    - name: rm -f /etc/rsyslog.d/sdlog.conf && systemctl restart rsyslog
