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

# Here we must create as the salt stack does not appear to allow us to create
# VMs with the class DispVM and attach the usb device specified in the config
# permanently to this VM
sd-export-create-named-dispvm:
  cmd.run:
    - name: >
        qvm-check sd-export-usb ||
        qvm-create --class DispVM --template sd-export-usb-dvm --label red sd-export-usb
    - require:
      - qvm: sd-export-usb-dvm

{% import_json "sd/config.json" as d %}

# Persistent attachments can only be removed when the domain is off, so we must
# kill sd-export-usb before detaching the USB devices from the domain
sd-export-named-dispvm-permanently-attach-usb:
  cmd.run:
    - name: >
        qvm-kill sd-export-usb || true ;
        qvm-usb detach sd-export-usb || true ;
        qvm-usb attach --persistent sd-export-usb {{ d.usb.device }} || true
    - require:
      - cmd: sd-export-create-named-dispvm

sd-export-named-dispvm-add-tags:
  qvm.vm:
    - name: sd-export-usb
    - tags:
      - add:
        - sd-workstation
    - require:
      - cmd: sd-export-create-named-dispvm
