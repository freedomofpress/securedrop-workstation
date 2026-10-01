# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Creates the 'sd-admin' AppVM to provide tooling for admin operations
# against SecureDrop Servers (as opposed to against SecureDrop Workstation).
#
# Currently it uses sys-firewall for networking; we'll need to test
# direct connections to the hardware firewall, as well as configure Torified access.
##

include:
  - admin_salt.sd-admin-template

sd-admin:
  qvm.vm:
    - name: sd-admin
    - present:
      - label: red
      - template: sd-admin-debian-13
    - prefs:
      - template: sd-admin-debian-13
      - netvm: sys-firewall
      - autostart: false
      - default_dispvm: ""
      - virt-mode: pvh
      - kernel: "pvgrub2-pvh"
    - tags:
      - add:
        - sd-workstation
        - sd-admin
    - features:
      - enable:
        - service.paxctld
    - require:
      - qvm: sd-admin-debian-13

sd-admin-custom-persist:
  qvm.features:
    - name: sd-admin
    - enable:
      - service.custom-persist
    - set:
      - custom-persist.tor_data: dir:debian-tor:debian-tor:0700:/var/lib/tor
      - custom-persist.tor_config: dir:root:root:0700:/etc/tor
      - custom-persist.home: /home
