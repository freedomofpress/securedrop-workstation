# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

#
# Installs 'sd-export' AppVM, to persistently store SD data
# This VM has no network configured.
##
include:
  - sd-workstation-template
  - sd-upgrade-templates

sd-export-template:
  qvm.vm:
    - name: sd-export-buster-template
    - clone:
      - source: securedrop-workstation-buster
      - label: red
    - tags:
      - add:
        - sd-workstation
        - sd-workstation-updates
    - require:
      - sls: sd-workstation-template
      - sls: sd-upgrade-templates

sd-export-usb-dvm:
  qvm.vm:
    - name: sd-export-usb-dvm
    - present:
      - template: sd-export-buster-template
      - label: red
    - prefs:
      - template: sd-export-buster-template
      - netvm: ""
      - template_for_dispvms: True
    - tags:
      - add:
        - sd-workstation
        - sd-buster
    - features:
      - enable:
        - service.paxctld
    - require:
      - qvm: sd-export-buster-template

# Ensure the Qubes menu is populated with relevant app entries,
# so that Nautilus/Files can be started via GUI interactions.
sd-export-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start --skip-if-running sd-export-buster-template &&
        qvm-sync-appmenus sd-export-buster-template
    - require:
      - qvm: sd-export-buster-template
    - onchanges:
      - qvm: sd-export-buster-template

sd-export-create-named-dispvm:
  qvm.vm:
    - name: sd-export-usb
    - present:
      - template: sd-export-usb-dvm
      - class: DispVM
      - label: red
    - tags:
      - add:
        - sd-workstation
    - require:
      - qvm: sd-export-usb-dvm
