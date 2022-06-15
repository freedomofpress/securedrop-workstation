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
{% from 'sd-default-config.sls' import sdvars with context %}

include:
  - sd-workstation-template
  - sd-upgrade-templates

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
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: sd-workstation-template
      - sls: sd-upgrade-templates
