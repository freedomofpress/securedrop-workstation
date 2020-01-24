# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
sys-firewall-rpm-test-key:
  file.managed:
    - name: /rw/config/RPM-GPG-KEY-securedrop-workstation
    - source: "salt://sd/sd-workstation/apt-test-pubkey.asc"
    - user: root
    - group: root
    - mode: 644

sys-firewall-rpm-test-key-script:
  file.managed:
    - name: /rw/config/sd-copy-rpm-repo-pubkey.sh
    - source: "salt://sd/sys-firewall/sd-copy-rpm-repo-pubkey.sh"
    - user: root
    - group: root
    - mode: 755

sys-firewall-rpm-test-key-rclocal:
  file.append:
    - name: /rw/config/rc.local
    - text: "/rw/config/sd-copy-rpm-repo-pubkey.sh"

sys-firewall-rpm-test-key-import:
  cmd.run:
    - name: /rw/config/sd-copy-rpm-repo-pubkey.sh
    - require:
      - file: sys-firewall-rpm-test-key
      - file: sys-firewall-rpm-test-key-script
