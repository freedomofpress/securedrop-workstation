# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.work
# ========
#
# Installs 'sd-app' AppVM, to persistently store SD data
# This VM has no network configured.
##
include:
  - sd-workstation-template
  - sd-upgrade-templates

sd-app-template:
  qvm.vm:
    - name: sd-app-buster-template
    - clone:
      - source: securedrop-workstation-buster
      - label: yellow
    - tags:
      - add:
        - sd-workstation
        - sd-buster
        - sd-workstation-updates
    - require:
      - sls: sd-workstation-template
      - sls: sd-upgrade-templates

sd-app:
  qvm.vm:
    - name: sd-app
    - present:
      - label: yellow
    - prefs:
      - template: sd-app-buster-template
      - netvm: ""
    - tags:
      - add:
        - sd-client
        - sd-workstation
    - features:
      - enable:
        - service.paxctld
    - require:
      - qvm: sd-app-buster-template

# Ensure the Qubes menu is populated with relevant app entries,
# so that Nautilus/Files can be started via GUI interactions.
sd-app-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start --skip-if-running sd-app-buster-template &&
        qvm-sync-appmenus sd-app-buster-template
    - require:
      - qvm: sd-app-buster-template
    - onchanges:
      - qvm: sd-app-buster-template
