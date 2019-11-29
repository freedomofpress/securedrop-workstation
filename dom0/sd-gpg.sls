# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-gpg
# ========
#
# Installs 'sd-gpg' AppVM, to implement split GPG for SecureDrop
# This VM has no network configured.
##

include:
  - sd-workstation-template

sd-gpg:
  qvm.vm:
    - name: sd-gpg
    - present:
      - template: securedrop-workstation-buster
      - label: purple
    - prefs:
      - template: securedrop-workstation-buster
      - netvm: ""
      - autostart: true
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: sd-workstation-template
      - sls: sd-upgrade-templates
