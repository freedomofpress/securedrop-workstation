# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-admin-vault
# ========
#
# Sets up networkless AppVM for securedrop-administrator's secrets.
#
#

include:
  - admin_salt.sd-admin-template

sd-admin-vault:
  qvm.vm:
    - name: sd-admin-vault
    - present:
      - label: black
      - template: sd-admin-debian-13
    - prefs:
      - template: sd-admin-debian-13
      - netvm: ""
      - autostart: false
      - default_dispvm: ""
      - virt-mode: pvh
      - kernel: "pvgrub2-pvh"
    - features:
      - enable:
        - service.paxctld
      - set:
        - menu-items: "org.keepassxc.KeePassXC.desktop"
    - tags:
      - add:
        - sd-workstation
        - sd-admin
    - require:
      - qvm: sd-admin-debian-13

