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
  - sd-templates
  - sd-upgrade-templates

sd-gpg:
  qvm.vm:
    - name: sd-gpg
    - present:
      - template: sd-small-buster-template
      - label: purple
    - prefs:
      - template: sd-small-buster-template
      - netvm: ""
      - autostart: true
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: sd-workstation-template
      - sls: sd-upgrade-templates
      - sls: sd-templates
