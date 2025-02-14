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

# Set a backup passphrase for the logs in sd-log.
# Hardcoding a backup passphrase is to automate the backup/vm-rebuild
# process, and is not a security measure. This passphrase will only be
# used in this instance, and not for general system backups.
{% set pass = "SDW_SDLOG" %}
{% set artifact_vm = "sd-retain-logvm" %}
{% set backup_dest = "/home/user/SDLog_Backup/" %}

# Set "install epoch". Bump this number to backup and rebuild this vm.
# This is more of a tag than a numerical value, and should not
# be used for anything other than an equality check.
{% set sdlog_epoch = '1001' %}

include:
  - securedrop_salt.sd-workstation-template

# If sd-log exists but fails a freshness check, create a VM to
# archive it, then back up and rebuild it
install-{{ artifact_vm }}:
  qvm.vm:
    - name: {{ artifact_vm }}
    - present:
      - label: red
    - prefs:
      - netvm: ""
      - default_dispvm: ""
      - include_in_backups: False
      - qrexec_timeout: 180
    - onlyif:
      - qvm-check --quiet sd-log
    - unless:
      - (( `qvm-features sd-log sd-install-epoch` == {{ sdlog_epoch }} ))

# Size backup vm, create backup directory (starts backup vm), create backup.
# Backup passphrase must be passed via stdin or written to disk; here we pass
# via stdin.
{{ artifact_vm }}-prepare-backup:
  cmd.run:
    - names:
      - qvm-volume resize {{ artifact_vm }}:private {{ d.vmsizes.sd_log }}GiB
      - qvm-run {{ artifact_vm }} 'mkdir -p -m 755 {{ backup_dest }}'
      - echo {{ pass }} | qvm-backup -y -q -d {{ artifact_vm }} -p - {{ backup_dest }} sd-log
      - qvm-shutdown --force --wait {{ artifact_vm }}
    - require:
      - cmd: sd-log-poweroff
    - onlyif:
      - qvm-check --quiet sd-log
      - qvm-check --quiet {{ artifact_vm }}
    - unless:
      - (( `qvm-features sd-log sd-install-epoch` == {{ sdlog_epoch }} ))

sd-log-poweroff:
  cmd.run:
    - name: qvm-shutdown --force --wait sd-log
    - onlyif:
      - qvm-check --quiet sd-log

sd-log-remove-if-stale:
  qvm.absent:
    - name: sd-log
    - require:
      - cmd: {{ artifact_vm }}-prepare-backup
    - onlyif:
      - qvm-check --quiet sd-log
    - unless:
      - (( `qvm-features sd-log sd-install-epoch` == {{ sdlog_epoch }} ))

# Install sd-log.
# This state declares the {{ artifact_vm}}-prepare-backup state as
# a requisite; if the state is skipped due to its own constraints
# (`onlyif`), the requirement is still considered satisfied.
# If this state is unsuccessful, with failhard=True the highstate
# will fail by design.
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
      - cmd: {{ artifact_vm }}-prepare-backup
    - failhard: True

# The private volume size should be set in config.json
sd-log-private-volume-size:
  cmd.run:
    - name: >
        qvm-volume resize sd-log:private {{ d.vmsizes.sd_log }}GiB
    - onchanges:
      - qvm: install-sd-log
