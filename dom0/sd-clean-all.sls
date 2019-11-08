# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

set-fedora-as-default-dispvm:
  cmd.run:
    - name: qvm-check fedora-30-dvm && qubes-prefs default_dispvm fedora-30-dvm || qubes-prefs default_dispvm ''

{% set gui_user = salt['cmd.shell']('groupmems -l -g qubes') %}

include:
  - sd-usb-autoattach-remove

remove-dom0-sdw-config-files:
  file.absent:
    - names:
      - /opt/securedrop
      - /etc/yum.repos.d/securedrop-workstation-dom0.repo
      - /usr/bin/securedrop-update
      - /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation
      - /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test
      - /etc/cron.daily/securedrop-update-cron
      - /srv/salt/securedrop-update
      - /usr/share/securedrop/icons
      - /home/{{ gui_user }}/.config/autostart/SDWLogin.desktop
      - /usr/bin/securedrop-login
      - /etc/qubes-rpc/policy/securedrop.Log
      - /etc/qubes-rpc/policy/securedrop.Proxy
      - /home/{{ gui_user }}/Desktop/securedrop-launcher.desktop
      - /home/{{ gui_user }}/.securedrop_launcher

sd-cleanup-crontab:
  file.replace:
    - name: /etc/crontab
    - pattern: '### BEGIN securedrop-workstation ###.*### END securedrop-workstation ###\s*'
    - flags:
      - MULTILINE
      - DOTALL
    - repl: ''
    - backup: no

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
