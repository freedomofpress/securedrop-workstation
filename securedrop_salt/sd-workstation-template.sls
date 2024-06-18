# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}

include:
  - securedrop_salt.sd-base-template

# Installs consolidated templateVMs:
# Sets virt_mode and kernel to use custom hardened kernel.
# - sd-small-{{ sdvars.distribution }}-template, to be used for
#   sd-app, sd-gpg, sd-log, and sd-proxy
# - sd-large-{{ sdvars.distribution }}-template, to be used for
#   sd-export and sd-viewer
sd-small-{{ sdvars.distribution }}-template:
  qvm.vm:
    - name: sd-small-{{ sdvars.distribution }}-template
    - clone:
      - source: sd-base-{{ sdvars.distribution }}-template
      - label: red
    - prefs:
      - virt-mode: pvh
      - kernel: 'pvgrub2-pvh'
      - default_dispvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - features:
      - enable:
        - service.paxctld
    - require:
      - sls: securedrop_salt.sd-base-template

sd-large-{{ sdvars.distribution }}-template:
  qvm.vm:
    - name: sd-large-{{ sdvars.distribution }}-template
    - clone:
      - source: sd-base-{{ sdvars.distribution }}-template
      - label: red
    - prefs:
      - virt-mode: pvh
      - kernel: 'pvgrub2-pvh'
      - default_dispvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - features:
      - enable:
        - service.paxctld
    - require:
      - sls: securedrop_salt.sd-base-template
