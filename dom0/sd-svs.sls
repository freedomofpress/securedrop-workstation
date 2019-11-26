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
    - name: sd-svs-buster-template
    - clone:
      - source: securedrop-workstation-buster
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
      - template: sd-svs-buster-template
      - label: yellow
    - prefs:
      - netvm: ""
      - template: sd-svs-buster-template
    - tags:
      - add:
        - sd-client
        - sd-workstation
    - features:
      - enable:
        - service.paxctld
    - require:
      - qvm: sd-svs-template

# Ensure the Qubes menu is populated with relevant app entries,
# so that Nautilus/Files can be started via GUI interactions.
sd-svs-buster-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start --skip-if-running sd-svs-buster-template &&
        qvm-sync-appmenus sd-svs-buster-template
    - require:
      - qvm: sd-svs-template
    - onchanges:
      - qvm: sd-svs-template
