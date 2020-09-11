# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

#
# Installs 'sd-devices' AppVM, to persistently store SD data
# This VM has no network configured.
##
include:
  - sd-workstation-template
  - sd-upgrade-templates

sd-devices-dvm:
  qvm.vm:
    - name: sd-devices-dvm
    - present:
      - template: sd-large-buster-template
      - label: red
    - prefs:
      - template: sd-large-buster-template
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
      - qvm: sd-large-buster-template

# Ensure the Qubes menu is populated with relevant app entries,
# so that Nautilus/Files can be started via GUI interactions.
sd-devices-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start --skip-if-running sd-large-buster-template &&
        qvm-sync-appmenus sd-large-buster-template
    - require:
      - qvm: sd-large-buster-template
    - onchanges:
      - qvm: sd-large-buster-template

sd-devices-create-named-dispvm:
  qvm.vm:
    - name: sd-devices
    - present:
      - template: sd-devices-dvm
      - class: DispVM
      - label: red
    - tags:
      - add:
        - sd-workstation
    - require:
      - qvm: sd-devices-dvm
