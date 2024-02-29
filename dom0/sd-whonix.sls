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
{% from 'sd-default-config.sls' import sdvars with context %}

include:
  - sd-upgrade-templates

sd-whonix:
  qvm.vm:
    - name: sd-whonix
    - present:
      - label: purple
      - mem: 500
    - prefs:
      - template: whonix-gateway-17
      - provides-network: true
      - netvm: "sys-firewall"
      - autostart: true
      - kernelopts: "nopat apparmor=1 security=apparmor"
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - require:
      - sls: sd-upgrade-templates

{% import_json "sd/config.json" as d %}

sd-proxy-config:
  qvm.features:
    - set:
        # TODO: sd-whonix:/var/lib/tor/keys/app_journalist.auth_private
        - vm-config.SD_HIDSERV_HOSTNAME: {{ d.hidserv.hostname }}
        - vm-config.SD_HIDSERV_KEY: {{ d.hidserv.key }}
