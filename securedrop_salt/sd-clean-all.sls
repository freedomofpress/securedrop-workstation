# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

{% import_json "securedrop_salt/config.json" as d %}

set-fedora-as-default-dispvm:
  cmd.run:
    - name: qvm-check default-dvm && qubes-prefs default_dispvm default-dvm || qubes-prefs default_dispvm ''

{% set gui_user = salt['cmd.shell']('groupmems -l -g qubes') %}
{% set gui_user_id = salt['cmd.shell']('id -u ' + gui_user) %}

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

# autoattach modifications are only present in sd-fedora-40-dvm
# so no more sd-usb-autoattach-remove necessary
remove-sd-fedora-dispvm:
  qvm.absent:
    - name: sd-fedora-40-dvm
    - require:
      - qvm: restore-sys-usb-dispvm
{% else %}
# If sys-usb is not disposable, clean up after ourselves
include:
  - securedrop_salt.sd-usb-autoattach-remove
{% endif %}

# Removes all salt-provisioned files (if these files are also provisioned via
# RPM, they should be removed as part of remove-dom0-sdw-config-files-dev)
remove-dom0-sdw-config-files:
  file.absent:
    - names:
      - /etc/yum.repos.d/securedrop-workstation-dom0.repo
      - /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation
      - /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test
      - /home/{{ gui_user }}/.config/autostart/press.freedom.SecureDropUpdater.desktop
      - /home/{{ gui_user }}/Desktop/press.freedom.SecureDropUpdater.desktop
      - /home/{{ gui_user }}/.securedrop_updater
      - /var/lib/securedrop-workstation

# Remove any custom RPC policy tags added to non-SecureDrop VMs by the user
remove-rpc-policy-tags:
  cmd.script:
    - name: salt://securedrop_salt/remove-tags.py

sd-cleanup-sys-firewall:
  cmd.run:
    - names:
      - qvm-run sys-firewall 'sudo rm -f /rw/config/RPM-GPG-KEY-securedrop-workstation'
      - qvm-run sys-firewall 'sudo rm -f /rw/config/RPM-GPG-KEY-securedrop-workstation-test'
      - qvm-run sys-firewall 'sudo rm -f /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation'
      - qvm-run sys-firewall 'sudo rm -f /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test'

sd-cleanup-whonix-gateway:
  cmd.run:
    - names:
      - qvm-run whonix-gateway-17 'sudo apt purge --yes securedrop-keyring securedrop-qubesdb-tools securedrop-whonix-config'
      - qvm-run whonix-gateway-17 'sudo rm -f /etc/apt/sources.list.d/apt-test_freedom_press.sources'

# Reset desktop icon size to its original value
dom0-reset-icon-size-xfce:
  cmd.script:
    - name: /usr/bin/securedrop/update-xfce-settings
    - args: reset-icon-size
    - runas: {{ gui_user }}

# Reset power management options to their original values
{% if d.environment == "prod" or d.environment == "staging" %}
dom0-reset-power-management-xfce:
  cmd.script:
    - name: /usr/bin/securedrop/update-xfce-settings
    - args: reset-power-management
    - runas: {{ gui_user }}
{% endif %}
