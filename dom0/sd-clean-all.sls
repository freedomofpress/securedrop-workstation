# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

{% import_json "sd/config.json" as d %}

set-fedora-as-default-dispvm:
  cmd.run:
    - name: qvm-check default-dvm && qubes-prefs default_dispvm default-dvm || qubes-prefs default_dispvm ''

{% set gui_user = salt['cmd.shell']('groupmems -l -g qubes') %}

{% if salt['pillar.get']('qvm:sys-usb:disposable', true) %}
restore-sys-usb-dispvm-halt:
  qvm.kill:
    - name: sys-usb

restore-sys-usb-dispvm-halt-wait:
  cmd.run:
    - name: sleep 5
    - require:
      - qvm: restore-sys-usb-dispvm-halt

restore-sys-usb-dispvm:
  qvm.prefs:
    - name: sys-usb
    - template: default-dvm
    - require:
      - cmd: restore-sys-usb-dispvm-halt-wait
      - cmd: set-fedora-as-default-dispvm

restore-sys-usb-dispvm-start:
  qvm.start:
    - name: sys-usb
    - require:
      - qvm: restore-sys-usb-dispvm

# autoattach modifications are only present in sd-fedora-39-dvm
# so no more sd-usb-autoattach-remove necessary
remove-sd-fedora-dispvm:
  qvm.absent:
    - name: sd-fedora-39-dvm
    - require:
      - qvm: restore-sys-usb-dispvm
{% else %}
# If sys-usb is not disposable, clean up after ourselves
include:
  - sd-usb-autoattach-remove
{% endif %}

# Reset desktop icon size to its original value
dom0-reset-icon-size-xfce:
  cmd.script:
    - name: salt://update-xfce-settings
    - args: reset-icon-size
    - runas: {{ gui_user }}

# Reset power management options to their original values
{% if d.environment == "prod" or d.environment == "staging" %}
dom0-reset-power-management-xfce:
  cmd.script:
    - name: salt://update-xfce-settings
    - args: reset-power-management
    - runas: {{ gui_user }}
{% endif %}

# Removes all salt-provisioned files (if these files are also provisioned via
# RPM, they should be removed as part of remove-dom0-sdw-config-files-dev)
remove-dom0-sdw-config-files:
  file.absent:
    - names:
      - /etc/yum.repos.d/securedrop-workstation-dom0.repo
      - /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation
      - /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test
      - /usr/share/securedrop/icons
      - /home/{{ gui_user }}/.config/autostart/SDWLogin.desktop
      - /usr/bin/securedrop-login
      - /etc/qubes-rpc/policy/securedrop.Log
      - /etc/qubes-rpc/policy/securedrop.Proxy
      - /home/{{ gui_user }}/Desktop/securedrop-launcher.desktop
      - /home/{{ gui_user }}/.securedrop_launcher
      - /srv/salt/qa-switch.tar.gz
      - /srv/salt/qa-switch
      - /srv/salt/consolidation-qa-switch.sh
      - /etc/qubes/policy.d/60-securedrop-workstation.policy
      - /etc/qubes/policy.d/70-securedrop-workstation.policy

# Remove any custom RPC policy tags added to non-SecureDrop VMs by the user
remove-rpc-policy-tags:
  cmd.script:
    - name: salt://remove-tags

sd-cleanup-etc-changes:
  file.replace:
    - names:
      - /etc/crontab
      - /etc/systemd/logind.conf
      - /etc/qubes/repo-templates/qubes-templates.repo
    - pattern: '### BEGIN securedrop-workstation ###.*### END securedrop-workstation ###\s*'
    - flags:
      - MULTILINE
      - DOTALL
    - repl: ''
    - backup: no

{% if d.environment == "prod" or d.environment == "staging" %}
apply-systemd-changes:
  cmd.run:
    - name: sudo systemctl restart systemd-logind
{% endif %}

sd-cleanup-sys-firewall:
  cmd.run:
    - names:
      - qvm-run sys-firewall 'sudo rm -f /rw/config/RPM-GPG-KEY-securedrop-workstation'
      - qvm-run sys-firewall 'sudo rm -f /rw/config/RPM-GPG-KEY-securedrop-workstation-test'
      - qvm-run sys-firewall 'sudo rm -f /rw/config/sd-copy-rpm-repo-pubkey.sh'
      - qvm-run sys-firewall 'sudo rm -f /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation'
      - qvm-run sys-firewall 'sudo rm -f /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test'
      - qvm-run sys-firewall 'sudo perl -pi -E "s#^/rw/config/sd-copy-rpm-repo-pubkey.sh##" /rw/config/rc.local'

sd-cleanup-rpc-mgmt-policy:
  file.replace:
    - names:
      - /etc/qubes-rpc/policy/qubes.VMShell
      - /etc/qubes-rpc/policy/qubes.VMRootShell
    - repl: ''
    - ignore_if_missing: True
    - pattern: '^disp-mgmt-sd-\w+\s+sd-\w+\s+allow,user=root'

{% set sdw_customized_rpc_files = salt['cmd.shell']('grep -rIl "BEGIN securedrop-workstation" /etc/qubes-rpc/ | cat').splitlines() %}
{% if sdw_customized_rpc_files|length > 0 %}
sd-cleanup-rpc-policy-grants:
  file.replace:
    - names: {{ sdw_customized_rpc_files }}
    - pattern: '### BEGIN securedrop-workstation ###.*### END securedrop-workstation ###\s*'
    - flags:
      - MULTILINE
      - DOTALL
    - repl: ''
    - backup: no
{% endif %}
