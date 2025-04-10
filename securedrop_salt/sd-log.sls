# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

#
# Installs 'sd-log' AppVM for collecting and storing logs
# from all SecureDrop related VMs.
# This VM has no network configured.
##

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}

# Check environment
{% import_json "securedrop_salt/config.json" as d %}

# Set "install epoch". Bump this number to backup and rebuild this vm.
# This is more of a tag than a numerical value, and should not
# be used for anything other than an equality check.
{% set sdlog_epoch = '1001' %}

include:
  - securedrop_salt.sd-workstation-template

sd-log-epoch-bump-shutdown:
  qvm.shutdown:
    - name: sd-log
    - flags:
      - force
      - wait
    - onlyif:
      - qvm-check --quiet sd-log
    - unless:
      - (( `qvm-features sd-log sd-install-epoch` == {{ sdlog_epoch }} ))

sd-log-epoch-bump-remove:
  qvm.absent:
    - name: sd-log
    - require:
      - qvm: sd-log-epoch-bump-shutdown
    - onlyif:
      - qvm-check --quiet sd-log
    - unless:
      - (( `qvm-features sd-log sd-install-epoch` == {{ sdlog_epoch }} ))

install-sd-log:
  qvm.vm:
    - name: sd-log
    - present:
      # Sets attributes if creating VM for the first time,
      # otherwise `prefs` must be used.
      # Label color is set during initial configuration but
      # not enforced on every Salt run, in case of user customization.
      - label: red
      - template: sd-small-{{ sdvars.distribution }}-template
    - prefs:
      - template: sd-small-{{ sdvars.distribution }}-template
      - netvm: ""
      - autostart: true
      - default_dispvm: ""
    - tags:
      - add:
        - sd-workstation
    - features:
      - enable:
        - service.paxctld
        - service.redis
        - service.securedrop-logging-disabled
        - service.securedrop-log-server
      - set:
        - sd-install-epoch: {{ sdlog_epoch }}
        - menu-items: "org.gnome.Nautilus.desktop"
    - require:
      - qvm: sd-small-{{ sdvars.distribution }}-template

# The private volume size should be set in config.json
sd-log-private-volume-size:
  cmd.run:
    - name: >
        qvm-volume resize sd-log:private {{ d.vmsizes.sd_log }}GiB
    - onchanges:
      - qvm: install-sd-log
