# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

#
# Installs 'sd-log' AppVM for collecting and storing logs
# from all SecureDrop related VMs.
# This VM has no network configured.
##

# Imports "sdvars" for environment config
{% from 'sd-default-config.sls' import sdvars with context %}

include:
  - sd-workstation-template
  - sd-upgrade-templates

sd-log:
  qvm.vm:
    - name: sd-log
    - present:
      - template: sd-small-{{ sdvars.distribution }}-template
      - label: red
    - prefs:
      - template: sd-small-{{ sdvars.distribution }}-template
      - netvm: ""
      - autostart: true
    - tags:
      - add:
        - sd-workstation
    - features:
      - enable:
        - service.paxctld
        - service.redis
        - service.securedrop-log
    - require:
      - qvm: sd-small-{{ sdvars.distribution }}-template

{% import_json "sd/config.json" as d %}

# The private volume size should be set in config.json
sd-log-private-volume-size:
  cmd.run:
    - name: >
        qvm-volume resize sd-log:private {{ d.vmsizes.sd_log }}GiB
    - require:
      - qvm: sd-log
