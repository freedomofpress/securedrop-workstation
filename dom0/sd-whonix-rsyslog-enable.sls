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


# We can not place the file on the template under /etc/rsyslog.d/ because of whonix
# template. This sdlog.conf file is the same from the securedrop-log package, to
# make sure that rsyslogd use our logging plugin.
sd-rsyslog-sdlog-conf-for-sd-whonix:
  file.managed:
    - name: /rw/config/sdlog.conf
    - source: "salt://sdlog.conf"

# Because whonix-gw-15 template is not allowing to create the config file on
# package install time, we do it via rc.local call.
sd-rc-enable-logging:
  file.blockreplace:
    - name: /rw/config/rc.local
    - append_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        # Add sd-rsyslog.conf file for syslog
        ln -sf /rw/config/sd-rsyslog.conf /etc/sd-rsyslog.conf
        if [ ! -f /etc/rsyslog.d/sdlog.conf ]; then
            ln -sf /rw/config/sdlog.conf /etc/rsyslog.d/sdlog.conf
        fi
        systemctl restart rsyslog
  cmd.run:
    - name: ln -sf /rw/config/sd-rsyslog.conf /etc/sd-rsyslog.conf && systemctl restart rsyslog


