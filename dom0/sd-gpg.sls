# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-gpg
# ========
#
# Installs 'sd-gpg' AppVM, to implement split GPG for SecureDrop
# This VM has no network configured.
##

sd-gpg:
  qvm.vm:
    - name: sd-gpg
    - present:
      - template: sd-workstation-template
      - label: purple
    - prefs:
      - netvm: ""
    - tags:
      - add:
        - sd-workstation
    - require:
      - qvm: sd-workstation-template
