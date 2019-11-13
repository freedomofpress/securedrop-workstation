# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

#
# Installs 'sd-export' AppVM, to persistently store SD data
# This VM has no network configured.
##
include:
  - sd-workstation-template

sd-export-template:
  qvm.vm:
    - name: sd-export-template
    - clone:
      - source: securedrop-workstation
      - label: red
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: sd-workstation-template

sd-export-usb-dvm:
  qvm.vm:
    - name: sd-export-usb-dvm
    - present:
      - template: sd-export-template
      - label: red
    - prefs:
      - netvm: ""
      - template_for_dispvms: True
    - tags:
      - add:
        - sd-workstation
    - features:
      - enable:
        - service.paxctld
    - require:
      - qvm: sd-export-template

# Ensure the Qubes menu is populated with relevant app entries,
# so that Nautilus/Files can be started via GUI interactions.
sd-export-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start --skip-if-running sd-export-template &&
        qvm-sync-appmenus sd-export-template
    - require:
      - qvm: sd-export-template
    - onchanges:
      - qvm: sd-export-template

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
