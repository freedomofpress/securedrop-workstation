# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-gpg
# ========
#
# Installs 'sd-gpg' AppVM, to implement split GPG for SecureDrop
# This VM has no network configured.
##

# Imports "apt_config" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import apt_config with context %}

# Check environment
{% import_json "securedrop_salt/config.json" as d %}

include:
  - securedrop_salt.sd-workstation-template
  - securedrop_salt.sd-upgrade-templates

sd-gpg:
  qvm.vm:
    - name: sd-gpg
    - present:
      # Sets attributes if creating VM for the first time,
      # otherwise `prefs` must be used.
      # Label color is set during initial configuration but
      # not enforced on every Salt run, in case of user customization.
      - label: purple
      - template: sd-small-{{ apt_config.distribution }}-template
    - prefs:
      - template: sd-small-{{ apt_config.distribution }}-template
      - netvm: ""
      - autostart: true
      - default_dispvm: ""
    - features:
      - enable:
        - service.securedrop-logging-disabled
      - set:
        - internal: ""
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: securedrop_salt.sd-workstation-template
      - sls: securedrop_salt.sd-upgrade-templates
