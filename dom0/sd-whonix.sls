# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.sd-whonix
# ==============
#
# Installs 'sd-whonix' ProxyVM for securedrop workstation.
#
##

include:
  # Import the upstream Qubes-maintained anon-whonix settings.
  # The anon-whonix config pulls in sys-whonix and sys-firewall,
  # as well as ensures the latest versions of Whonix are installed.
  - qvm.anon-whonix
  - sd-upgrade-templates

sd-whonix:
  qvm.vm:
    - name: sd-whonix
    - present:
      - label: purple
      - mem: 500
    - prefs:
      - template: whonix-gw-16
      - provides-network: true
      - netvm: "sys-firewall"
      - autostart: true
      - kernelopts: "nopat apparmor=1 security=apparmor"
    - tags:
      - add:
        - sd-workstation
        - sd-buster
    - require:
      - sls: qvm.anon-whonix
      - sls: sd-upgrade-templates
