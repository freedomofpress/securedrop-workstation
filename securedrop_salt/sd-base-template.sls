# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}

# Ensure debian-13-minimal is present for use as base template
dom0-install-debian-minimal-template:
  qvm.template_installed:
    - name: debian-13-minimal

# Clones a base templateVM from debian-13-minimal
sd-base-template:
  qvm.vm:
    - name: sd-base-debian-{{ sdvars.debian_version }}
    - clone:
      - source: debian-13-minimal
      - label: red
    - prefs:
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
      - qvm: dom0-install-debian-minimal-template
