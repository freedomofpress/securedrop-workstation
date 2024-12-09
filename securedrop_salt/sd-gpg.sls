# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-gpg
# ========
#
# Installs 'sd-gpg' AppVM, to implement split GPG for SecureDrop
# This VM has no network configured.
##

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}

# Check environment
{% import_json "securedrop_salt/config.json" as d %}

include:
  - securedrop_salt.sd-workstation-template
  - securedrop_salt.sd-upgrade-templates

sd-gpg:
  qvm.vm:
    - name: sd-gpg
    - present:
      - template: sd-small-{{ sdvars.distribution }}-template
      - label: purple
    - prefs:
      - template: sd-small-{{ sdvars.distribution }}-template
      - netvm: ""
      - autostart: true
      - default_dispvm: ""
    - features:
      - enable:
        - service.securedrop-logging-disabled
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: securedrop_salt.sd-workstation-template
      - sls: securedrop_salt.sd-upgrade-templates
