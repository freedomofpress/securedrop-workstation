# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Installs 'sd-proxy' AppVM, for managing connection between SecureDrop Client
# and the SecureDrop servers.
##

# Imports "sdvars" for environment config
{% from 'sd-default-config.sls' import sdvars with context %}

include:
  - sd-whonix
  - sd-upgrade-templates

sd-proxy:
  qvm.vm:
    - name: sd-proxy
    - present:
      - label: blue
    - prefs:
      - template: sd-small-{{ sdvars.distribution }}-template
      - netvm: sd-whonix
      - autostart: true
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - require:
      - qvm: sd-whonix
      - qvm: sd-small-{{ sdvars.distribution }}-template

# Permit the SecureDrop Proxy to manage Client connections
sd-proxy-dom0-securedrop.Proxy:
  file.prepend:
    - name: /etc/qubes-rpc/policy/securedrop.Proxy
    - text: |
        sd-app sd-proxy allow
        @anyvm @anyvm deny
