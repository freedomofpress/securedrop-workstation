# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Installs 'sd-proxy' AppVM, for managing connection between SecureDrop Client
# and the SecureDrop servers.
##

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}

include:
  - securedrop_salt.sd-whonix
  - securedrop_salt.sd-upgrade-templates

sd-proxy-dvm:
  qvm.vm:
    - name: sd-proxy-dvm
    - present:
      - label: blue
    - prefs:
      - template: sd-small-{{ sdvars.distribution }}-template
      - netvm: sd-whonix
      - template_for_dispvms: True
      - default_dispvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - require:
      - qvm: sd-whonix
      - qvm: sd-small-{{ sdvars.distribution }}-template

sd-proxy-create-named-dispvm:
  qvm.vm:
    - name: sd-proxy
    - present:
      - label: blue
      - class: DispVM
      - template: sd-proxy-dvm
    - prefs:
      - netvm: sd-whonix
      - autostart: true
      - default_dispvm: ""
    - features:
      - enable:
        - service.securedrop-mime-handling-default
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - require:
      - qvm: sd-proxy-dvm

{% import_json "securedrop_salt/config.json" as d %}

sd-proxy-config:
  qvm.features:
    - name: sd-proxy
    - set:
        - vm-config.SD_PROXY_ORIGIN: http://{{ d.hidserv.hostname }}
