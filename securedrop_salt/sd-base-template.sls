# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# Imports "apt_config" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import apt_config with context %}

include:
  - securedrop_salt.sd-dom0-files

# Clones a base templateVM from debian-12-minimal
sd-base-template:
  qvm.vm:
    - name: sd-base-{{ apt_config.distribution }}-template
    - clone:
      - source: debian-12-minimal
      - label: red
    - prefs:
      - default_dispvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-{{ apt_config.distribution }}
    - features:
      - enable:
        - service.paxctld
    - require:
      - qvm: dom0-install-debian-minimal-template
