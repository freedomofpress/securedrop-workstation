# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}

include:
  - securedrop_salt.sd-dom0-files

# Clones a base templateVM from debian-12-minimal
sd-base-template:
  qvm.vm:
    - name: sd-base-{{ sdvars.distribution }}-template
    - clone:
      - source: debian-12-minimal
      - label: red
    - prefs:
      - default_dispvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - features:
      - enable:
        - service.paxctld
    - require:
      - qvm: dom0-install-debian-minimal-template

{% if grains['osrelease'] != '4.2' %}
sd-base-template-deny-all-devices:
  cmd.run:
    - name: qvm-prefs sd-base-{{ sdvars.distribution }}-template devices_denied '*******'
{% endif %}
