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

sd-gpg:
  qvm.vm:
    - name: sd-gpg
    - present:
      # Sets attributes if creating VM for the first time,
      # otherwise `prefs` must be used.
      # Label color is set during initial configuration but
      # not enforced on every Salt run, in case of user customization.
      - label: purple
      - template: sd-inbox-debian-{{ sdvars.debian_version }}
    - prefs:
      - template: sd-inbox-debian-{{ sdvars.debian_version }}
      - netvm: ""
      - autostart: true
      - default_dispvm: ""
      - devices_denied: '*******'
    - features:
      - enable:
        - service.securedrop-logging-disabled
        - service.securedrop-gpg-dismiss-prompt
        - service.securedrop-get-secret-keys
      - set:
        - internal: ""
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: securedrop_salt.sd-workstation-template

sd-gpg-custom-persist:
  qvm.features:
    - name: sd-gpg
    - enable:
      - service.custom-persist
    - set:
      - custom-persist.gnupg_dir: dir:user:user:0700:/home/user/.gnupg
