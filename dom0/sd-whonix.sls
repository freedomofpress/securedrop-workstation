# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.sd-whonix
# ==============
#
# Installs 'sd-whonix' ProxyVM for securedrop journalist workstation.
#
##

include:
  - sd-dom0-files

sd-whonix-template:
  qvm.vm:
    - name: sd-whonix-template
    - clone:
      - source: whonix-gw-14
      - label: purple
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: sd-dom0-files

sd-whonix:
  qvm.vm:
    - name: sd-whonix
    - present:
      - template: sd-whonix-template
      - label: purple
      - mem: 500
    - prefs:
      - provides-network: true
      - netvm: "sys-firewall"
      - autostart: true
      - kernelopts: "nopat apparmor=1 security=apparmor"
    - tags:
      - add:
        - sd-workstation
    - require:
      - qvm: sd-whonix-template
