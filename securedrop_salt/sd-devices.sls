# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

#
# Installs 'sd-devices' AppVM, to persistently store SD data
# This VM has no network configured.
##

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}

include:
  - securedrop_salt.sd-workstation-template
  - securedrop_salt.sd-upgrade-templates

sd-devices-dvm:
  qvm.vm:
    - name: sd-devices-dvm
    - present:
      - template: sd-large-{{ sdvars.distribution }}-template
      - label: red
    - prefs:
      - template: sd-large-{{ sdvars.distribution }}-template
      - netvm: ""
      - template_for_dispvms: True
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - features:
      - enable:
        - service.paxctld
        - service.cups
    - require:
      - qvm: sd-large-{{ sdvars.distribution }}-template

# Ensure the Qubes menu is populated with relevant app entries,
# so that Nautilus/Files can be started via GUI interactions.
sd-devices-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start --skip-if-running sd-large-{{ sdvars.distribution }}-template &&
        qvm-sync-appmenus --force-root sd-large-{{ sdvars.distribution }}-template
    - require:
      - qvm: sd-large-{{ sdvars.distribution }}-template
    - onchanges:
      - qvm: sd-large-{{ sdvars.distribution }}-template

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
    - features:
      - enable:
        - service.securedrop-mime-handling
      - set:
        - vm-config.SD_MIME_HANDLING: sd-devices
    - require:
      - qvm: sd-devices-dvm
