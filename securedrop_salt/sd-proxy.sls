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
  - securedrop_salt.sd-workstation-template

sd-proxy-dvm:
  qvm.vm:
    - name: sd-proxy-dvm
    - present:
      # Sets attributes if creating VM for the first time,
      # otherwise `prefs` must be used.
      # Label color is set during initial configuration but
      # not enforced on every Salt run, in case of user customization.
      - label: blue
      - template: sd-small-{{ sdvars.distribution }}-template
    - prefs:
      - template: sd-small-{{ sdvars.distribution }}-template
      - netvm: sys-firewall
      - template_for_dispvms: True
      - default_dispvm: ""
      {% if grains['osrelease'] != '4.2' %}
      - devices_denied: '*******'
      {% endif %}
    - features:
      - set:
        {% if d.environment == "prod" %}
        - internal: 1
        {% else %}
        - internal: ""
        {% endif %}
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - require:
      - qvm: sd-small-{{ sdvars.distribution }}-template

sd-proxy-create-named-dispvm:
  qvm.vm:
    - name: sd-proxy
    - present:
      - label: blue
      - template: sd-proxy-dvm
      - class: DispVM
    - prefs:
      - template: sd-proxy-dvm
      - netvm: sys-firewall
      - autostart: true
      - default_dispvm: ""
      {% if grains['osrelease'] != '4.2' %}
      - devices_denied: '*******'
      {% endif %}
    - features:
      - enable:
        - service.securedrop-mime-handling
        - service.securedrop-arti
      - set:
          - vm-config.SD_MIME_HANDLING: default
          - servicevm: 1
          - internal: ""
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
        - vm-config.SD_PROXY_ORIGIN_KEY: {{ d.hidserv.key }}
    - require:
      - qvm: sd-proxy-create-named-dispvm
