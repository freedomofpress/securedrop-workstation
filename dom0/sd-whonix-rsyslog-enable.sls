# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Enables securedrop-log rsyslog plugin in sd-whonix
##

sd-rsyslog-for-sd-whonix:
  file.managed:
    - name: /rw/config/sd-rsyslog.conf
    - source: "salt://sd-rsyslog.conf.j2"
    - template: jinja
    - context:
        vmname: sd-whonix


sd-rc-enable-logging:
  file.blockreplace:
    - name: /rw/config/rc.local
    - append_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        # Add sd-rsyslog.conf file for syslog
        ln -sf /rw/config/sd-rsyslog.conf /etc/sd-rsyslog.conf
        systemctl restart rsyslog
  cmd.run:
    - name: ln -sf /rw/config/sd-rsyslog.conf /etc/sd-rsyslog.conf && systemctl restart rsyslog


