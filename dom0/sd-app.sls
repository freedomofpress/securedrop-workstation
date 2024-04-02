# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Installs 'sd-app' AppVM, to persistently store SD data
# This VM has no network configured.
##

# Imports "sdvars" for environment config
{% from 'sd-default-config.sls' import sdvars with context %}

include:
  - sd-workstation-template
  - sd-upgrade-templates

sd-app:
  qvm.vm:
    - name: sd-app
    - present:
      - label: yellow
    - prefs:
      - template: sd-small-{{ sdvars.distribution }}-template
      - netvm: ""
    - tags:
      - add:
        - sd-client
        - sd-workstation
    - features:
      - enable:
        - service.paxctld
    - require:
      - qvm: sd-small-{{ sdvars.distribution }}-template

{% import_json "sd/config.json" as d %}

# The private volume size should be defined in the config.json
sd-app-private-volume-size:
  cmd.run:
    - name: >
        qvm-volume resize sd-app:private {{ d.vmsizes.sd_app }}GiB
    - require:
      - qvm: sd-app

# Ensure the Qubes menu is populated with relevant app entries,
# so that Nautilus/Files can be started via GUI interactions.
sd-app-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start --skip-if-running sd-small-{{ sdvars.distribution }}-template &&
        qvm-sync-appmenus --force-root sd-small-{{ sdvars.distribution }}-template
    - require:
      - qvm: sd-small-{{ sdvars.distribution }}-template
    - onchanges:
      - qvm: sd-small-{{ sdvars.distribution }}-template
