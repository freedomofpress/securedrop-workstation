# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.sd-whonix
# ==============
#
# Installs 'sd-whonix' ProxyVM for SecureDrop Workstation.
# This VM will contain the Onion auth info to connect to the
# SecureDrop Application Server's Journalist API.
#
##

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}

{% import "qvm/whonix.jinja" as whonix %}

include:
  - securedrop_salt.sd-sys-whonix-vms

{% for vm in ['sd-proxy', 'sd-whonix'] %}
poweroff-{{ vm }}:
  qvm.shutdown:
    - name: {{ vm }}
    - flags:
      - force
      - wait
    - onlyif:
      - qvm-check --quiet {{ vm }}
    - unless:
      - qvm-prefs sd-whonix template | grep -q whonix-gateway-{{ whonix.whonix_version }}

{% endfor %}

sd-whonix:
  qvm.vm:
    - name: sd-whonix
    - present:
      - label: purple
      - template: whonix-gateway-{{ whonix.whonix_version }}
      - mem: 500
    - prefs:
      - template: whonix-gateway-{{ whonix.whonix_version }}
      - provides-network: true
      - netvm: "sys-firewall"
      - autostart: true
      - kernelopts: "apparmor=1 security=apparmor"
      - default_dispvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - features:
      - enable:
        - service.securedrop-whonix-config
    - require:
      - sls: securedrop_salt.sd-sys-whonix-vms

{% import_json "securedrop_salt/config.json" as d %}

sd-whonix-config:
  qvm.features:
    - name: sd-whonix
    - set:
        - vm-config.SD_HIDSERV_HOSTNAME: {{ d.hidserv.hostname }}
        - vm-config.SD_HIDSERV_KEY: {{ d.hidserv.key }}
        - menu-items: "anon_connection_wizard.desktop tor-control-panel.desktop"
