# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

{% if "template" in grains['id'] or grains['id'] in ["securedrop-workstation-buster", "sd-small-buster-template", "sd-large-buster-template", "whonix-gw-15"] %}
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

{% if grains['id'] in ["sd-small-buster-template", "sd-large-buster-template"] %}
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

{% else %}
# For all other VMs, configure to send to sd-log
configure-rsyslog-for-sd:
  file.managed:
    - name: /etc/sd-rsyslog.conf
    - source: "salt://sd-rsyslog.conf.j2"
{% endif %}

# Remove outdated configuration that was previously used to configure the
# sd-whonix VM name for logging purposes, see:
# https://github.com/freedomofpress/securedrop-workstation/issues/583
#
# Can be removed in a future release once all production workstations have
# been updated.
{% if grains['id'] == "sd-whonix" %}
sd-whonix-cleanup-rc-local:
  file.replace:
    - names:
      - /rw/config/rc.local
    - pattern: '### BEGIN securedrop-workstation ###.*### END securedrop-workstation ###\s*'
    - flags:
      - MULTILINE
      - DOTALL
    - repl: ''
    - backup: no

sd-whonix-cleanup-sdlog-conf:
  file.absent:
    - name: /rw/config/sdlog.conf
{% endif %}
