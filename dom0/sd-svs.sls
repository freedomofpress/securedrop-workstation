# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.work
# ========
#
# Installs 'sd-svs' AppVM, to persistently store SD data
# This VM has no network configured.
##
include:
  - sd-workstation-template

sd-svs-template:
  qvm.vm:
    - name: sd-svs-template
    - clone:
      - source: securedrop-workstation
      - label: yellow
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: sd-workstation-template

sd-svs:
  qvm.vm:
    - name: sd-svs
    - present:
      - template: sd-svs-template
      - label: yellow
    - prefs:
      - netvm: ""
    - tags:
      - add:
        - sd-workstation
    - require:
      - qvm: sd-svs-template

# Ensure the Qubes menu is populated with relevant app entries,
# so that Nautilus/Files can be started via GUI interactions.
sd-svs-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start --skip-if-running sd-svs-template &&
        qvm-sync-appmenus sd-svs-template
    - require:
      - qvm: sd-svs-template
    - onchanges:
      - qvm: sd-svs-template
