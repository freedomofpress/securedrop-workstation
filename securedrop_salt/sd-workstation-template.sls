# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# Imports "apt_config" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import apt_config with context %}

include:
  - securedrop_salt.sd-base-template

# Installs consolidated templateVMs:
# Sets virt_mode and kernel to use custom hardened kernel.
# - sd-small-{{ apt_config.distribution }}-template, to be used for
#   sd-app, sd-gpg, sd-log, and sd-proxy
# - sd-large-{{ apt_config.distribution }}-template, to be used for
#   sd-export and sd-viewer
sd-small-{{ apt_config.distribution }}-template:
  qvm.vm:
    - name: sd-small-{{ apt_config.distribution }}-template
    - clone:
      - source: sd-base-{{ apt_config.distribution }}-template
      - label: red
    - prefs:
      - virt-mode: pvh
      - kernel: 'pvgrub2-pvh'
      - default_dispvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-{{ apt_config.distribution }}
    - features:
      - enable:
        - service.paxctld
    - require:
      - sls: securedrop_salt.sd-base-template

sd-large-{{ apt_config.distribution }}-template:
  qvm.vm:
    - name: sd-large-{{ apt_config.distribution }}-template
    - clone:
      - source: sd-base-{{ apt_config.distribution }}-template
      - label: red
    - prefs:
      - virt-mode: pvh
      - kernel: 'pvgrub2-pvh'
      - default_dispvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-{{ apt_config.distribution }}
    - features:
      - enable:
        - service.paxctld
    - require:
      - sls: securedrop_salt.sd-base-template
