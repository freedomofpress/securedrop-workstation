# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

set-fedora-as-default-dispvm:
  cmd.run:
    - name: qubes-prefs default_dispvm fedora-30-dvm

remove-dom0-sdw-config-files:
  file.absent:
    - names:
      - /opt/securedrop
      - /etc/yum.repos.d/securedrop-workstation-dom0.repo
      - /usr/bin/securedrop-update
      - /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test
      - /etc/cron.daily/securedrop-update-cron
      - /usr/share/securedrop/icons

sd-cleanup-sys-firewall:
  cmd.run:
    - names:
      - qvm-run sys-firewall 'sudo rm -f /rw/config/RPM-GPG-KEY-securedrop-workstation-test'
      - qvm-run sys-firewall 'sudo rm -f /rw/config/sd-copy-rpm-repo-pubkey.sh'
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
