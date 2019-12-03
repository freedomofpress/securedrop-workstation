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
        - sd-buster
    - require:
      - sls: sd-workstation-template
      - sls: sd-upgrade-templates

sd-svs:
  qvm.vm:
    - name: sd-svs
    - present:
      - label: yellow
    - prefs:
      - template: sd-svs-buster-template
      - netvm: ""
    - tags:
      - add:
        - sd-client
        - sd-workstation
    - features:
      - enable:
        - service.paxctld
    - require:
      - qvm: sd-svs-buster-template

# Ensure the Qubes menu is populated with relevant app entries,
# so that Nautilus/Files can be started via GUI interactions.
sd-svs-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start --skip-if-running sd-svs-buster-template &&
        qvm-sync-appmenus sd-svs-buster-template
    - require:
      - qvm: sd-svs-buster-template
    - onchanges:
      - qvm: sd-svs-buster-template
