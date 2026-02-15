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
      - template: sd-admin-trixie-template
    - prefs:
      - template: sd-admin-trixie-template
      - netvm: sys-firewall
      - autostart: false
      - default_dispvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-admin
    - require:
      - qvm: sd-admin-trixie-template
