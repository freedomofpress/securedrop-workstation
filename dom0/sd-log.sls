# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

#
# Installs 'sd-log' AppVM for collecting and storing logs
# from all SecureDrop related VMs.
# This VM has no network configured.
##
include:
  - sd-workstation-template
  - sd-upgrade-templates

sd-log-template:
  qvm.vm:
    - name: sd-log-buster-template
    - clone:
      - source: securedrop-workstation-buster
      - label: red
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: sd-workstation-template

sd-log:
  qvm.vm:
    - name: sd-log
    - present:
      - template: sd-log-buster-template
      - label: red
    - prefs:
      - netvm: ""
      - autostart: true
    - tags:
      - add:
        - sd-workstation
    - features:
      - enable:
        - service.paxctld
    - require:
      - qvm: sd-log-buster-template

# Allow any SecureDrop VM to log to the centralized log VM
sd-log-dom0-securedrop.Log:
  file.prepend:
    - name: /etc/qubes-rpc/policy/securedrop.Log
    - text: |
        @tag:sd-workstation sd-log allow
        @anyvm @anyvm deny

{% import_json "sd/config.json" as d %}

# The private volume size should be set in config.json
sd-log-private-volume-size:
  cmd.run:
    - name: >
        qvm-volume resize sd-log:private {{ d.vmsizes.sd_log }}GiB
    - require:
      - qvm: sd-log
