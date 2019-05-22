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
      - source: sd-workstation-template
      - label: yellow
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: sd-workstation-template

sd-export-dvm:
  qvm.vm:
    - name: sd-export-dvm
    - present:
      - template: sd-export-template
      - label: yellow
    - prefs:
      - netvm: ""
      - template_for_dispvms: True
    - tags:
      - add:
        - sd-workstation
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

{% import_json "sd/config.json" as d %}

# Here we must create as the salt stack does not appear to allow us to create
# VMs with the class DispVM and attach the usb device specified in the config
# permanently to this VM
create-named-sd-export-dispvm-and-permanently-attach:
  cmd.run:
    - name: >
        qvm-remove --force sd-export-usb || true;
        qvm-create --class DispVM --template sd-export-dvm --label red sd-export-usb;
        qvm-usb attach --persistent sd-export-usb {{ d.usb.device }} || true;
