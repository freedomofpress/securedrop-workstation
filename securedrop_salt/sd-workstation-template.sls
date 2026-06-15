# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}

include:
  - securedrop_salt.sd-base-template

# Installs consolidated templateVMs:
# Sets virt_mode and kernel to use custom hardened kernel.
# - sd-small-debian-{{ sdvars.debian_version }}, to be used for
#   sd-app, sd-gpg, sd-log, and sd-proxy
# - sd-large-debian-{{ sdvars.debian_version }}, to be used for
#   sd-export and sd-viewer
sd-small-debian-{{ sdvars.debian_version }}:
  qvm.vm:
    - name: sd-small-debian-{{ sdvars.debian_version }}
    - clone:
      - source: sd-base-debian-{{ sdvars.debian_version }}
      - label: red
    - prefs:
      - virt-mode: pvh
      - kernel: 'pvgrub2-pvh'
      - default_dispvm: ""
      {% if grains['osrelease'] != '4.2' %}
      - devices_denied: '*******'
      {% endif %}
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - features:
      - enable:
        - service.paxctld
    - require:
      - sls: securedrop_salt.sd-base-template

sd-large-debian-{{ sdvars.debian_version }}:
  qvm.vm:
    - name: sd-large-debian-{{ sdvars.debian_version }}
    - clone:
      - source: sd-base-debian-{{ sdvars.debian_version }}
      - label: red
    - prefs:
      - virt-mode: pvh
      - kernel: 'pvgrub2-pvh'
      - default_dispvm: ""
      {% if grains['osrelease'] != '4.2' %}
      - devices_denied: '*******'
      {% endif %}
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - features:
      - enable:
        - service.paxctld
    - require:
      - sls: securedrop_salt.sd-base-template
