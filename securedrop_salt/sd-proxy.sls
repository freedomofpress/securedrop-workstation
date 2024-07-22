# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Installs 'sd-proxy' AppVM, for managing connection between SecureDrop Client
# and the SecureDrop servers.
##

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}
{% import_json "securedrop_salt/config.json" as d %}

include:
  - securedrop_salt.sd-whonix
  - securedrop_salt.sd-upgrade-templates
  - securedrop_salt.sd-workstation-template

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
  {% if d.environment == "prod" %}
    - features:
      - set:
        - internal: 1
  {% endif %}
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
        - service.securedrop-mime-handling
      - set:
          - vm-config.SD_MIME_HANDLING: default
          - servicevm: 1
      {% if d.environment == "prod" %}
          - internal: 1
      {% endif %}
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - require:
      - qvm: sd-proxy-dvm

sd-proxy-config:
  qvm.features:
    - name: sd-proxy
    - set:
        - vm-config.SD_PROXY_ORIGIN: http://{{ d.hidserv.hostname }}
    - require:
      - qvm: sd-proxy-create-named-dispvm
