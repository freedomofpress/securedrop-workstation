# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Installs 'sd-proxy' AppVM, for managing connection between SecureDrop Client
# and the SecureDrop servers.
##

# Imports "apt_config" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import apt_config with context %}
{% import_json "securedrop_salt/config.json" as d %}

include:
  - securedrop_salt.sd-whonix
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
      - template: sd-small-{{ apt_config.distribution }}-template
    - prefs:
      - template: sd-small-{{ apt_config.distribution }}-template
      - netvm: sd-whonix
      - template_for_dispvms: True
      - default_dispvm: ""
    - features:
      - set:
        {% if apt_config['env'] == "prod" %}
        - internal: 1
        {% else %}
        - internal: ""
        {% endif %}
    - tags:
      - add:
        - sd-workstation
        - sd-{{ apt_config.distribution }}
    - require:
      - qvm: sd-whonix
      - qvm: sd-small-{{ apt_config.distribution }}-template

sd-proxy-create-named-dispvm:
  qvm.vm:
    - name: sd-proxy
    - present:
      - label: blue
      - template: sd-proxy-dvm
      - class: DispVM
    - prefs:
      - template: sd-proxy-dvm
      - netvm: sd-whonix
      - autostart: true
      - default_dispvm: ""
    - features:
      - enable:
        - service.securedrop-mime-handling
      - set:
          - vm-config.SD_MIME_HANDLING: default
          - servicevm: 1
          {% if apt_config['env'] == "prod" %}
          - internal: 1
          {% else %}
          - internal: ""
          {% endif %}
    - tags:
      - add:
        - sd-workstation
        - sd-{{ apt_config.distribution }}
    - require:
      - qvm: sd-proxy-dvm

sd-proxy-config:
  qvm.features:
    - name: sd-proxy
    - set:
        - vm-config.SD_PROXY_ORIGIN: http://{{ d.hidserv.hostname }}
    - require:
      - qvm: sd-proxy-create-named-dispvm
