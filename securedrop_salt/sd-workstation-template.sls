# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}

include:
  - securedrop_salt.sd-base-template

# Installs consolidated templateVMs:
{% for template_prefix in ["sd-small", "sd-large"] %}
{{template_prefix}}-debian-{{ sdvars.debian_version }}:
  qvm.vm:
    - clone:
      - source: sd-base-debian-{{ sdvars.debian_version }}
      - label: red
    - prefs:
      # Sets virt_mode and kernel to use custom hardened kernel.
      - virt-mode: pvh
      - kernel: 'pvgrub2-pvh'
      - default_dispvm: ""
      - devices_denied: '*******'
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - features:
      - enable:
        - service.paxctld
    - require:
      - sls: securedrop_salt.sd-base-template
{% endfor %}
