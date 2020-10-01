# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

{% if "template" in grains['id'] or grains['id'] in ["securedrop-workstation-buster", "whonix-gw-15"] %}
include:
  - fpf-apt-test-repo

# Install securedrop-log package in TemplateVMs only
install-securedrop-log-package:
  pkg.installed:
    - pkgs:
      - securedrop-log
    - require:
      - sls: fpf-apt-test-repo
{% endif %}

{% if grains['id'] == "sd-log-buster-template" %}
install-redis-for-sd-log-template:
  pkg.installed:
    - pkgs:
      - redis-server
      - redis
remove-sd-rsyslog-config-for-logserver:
  file.absent:
    - name: /etc/rsyslog.d/sdlog.conf

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
  cmd.run:
    - name: /rw/config/rc.local
    - require:
      - file: sd-log-remove-rsyslog-qubes-plugin

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
{% else %}
# For all other VMs, configure to send to sd-log
configure-rsyslog-for-sd:
  file.managed:
    - name: /etc/sd-rsyslog.conf
    - source: "salt://sd-rsyslog.conf.j2"
{% endif %}

{% if grains['id'] == "whonix-gw-15" %}

# sd-log uses the hostname to sort logs into folders. Whonix enforces the name
# 'host' for anonymity reasons. For this reason, we set the 'localvm' value in
# sd-rsyslog.conf.
#
# rc.local in /rw of the AppVM is not a good option here, as it's run too late
# in the boot process. The template itself is prevented from logging via RPC
# policy (it's not tagged 'sd-workstation'), and we only base one AppVM on it,
# so we can safely set this value at the template level.
#
# Background:
# https://github.com/freedomofpress/securedrop-workstation/issues/583
sd-rsyslog-conf-for-sd-whonix:
  file.blockreplace:
    - name: /etc/sd-rsyslog.conf
    - append_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        localvm = sd-whonix
    - require:
        - file: configure-rsyslog-for-sd
{% endif %}
