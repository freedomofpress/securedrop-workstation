# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

{% if grains['id'] in ["securedrop-workstation-bullseye", "sd-small-bullseye-template", "sd-large-bullseye-template"] %}
include:
  - fpf-apt-repo

# Install securedrop-log package in TemplateVMs only
install-securedrop-log-package:
  pkg.installed:
    - pkgs:
      - securedrop-log
    - require:
      - sls: fpf-apt-repo

# configure all VMs to send to sd-log - excluded on a per-VM basis below via /rw
configure-rsyslog-for-sd:
  file.managed:
    - name: /etc/sd-rsyslog.conf
    - source: "salt://sd-rsyslog.conf.j2"

{% endif %}

{% if grains['id'] == "sd-small-{}-template".format(grains['oscodename']) %}
install-redis-for-sd-log-template:
  pkg.installed:
    - pkgs:
      - redis-server
      - redis

{% elif grains['id'] == "sd-log" %}
# Only for the "sd-log" AppVM, configure /rw/config to disable
# custom log config, and also start the necessary services.
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
        systemctl start redis
        systemctl start securedrop-log
        exit 0
  cmd.run:
    - name: /rw/config/rc.local
    - require:
      - file: sd-log-remove-rsyslog-qubes-plugin
remove-sd-rsyslog-config-for-logserver:
  file.absent:
    - name: /etc/rsyslog.d/sdlog.conf

{% elif grains['id'] == "sd-gpg" %}
# For sd-gpg, we disable logging altogether, since access
# to the keyring will be logged in sd-app
sd-gpg-remove-rsyslog-qubes-plugin:
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
    - name: /rw/config/rc.local
    - require:
      - file: sd-gpg-remove-rsyslog-qubes-plugin

{% endif %}
