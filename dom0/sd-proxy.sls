# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.work
# ========
#
# Installs 'sd-journlist' AppVM, for hosting the securedrop workstation app
#
##

include:
  - sd-whonix
  - sd-upgrade-templates

sd-proxy-template:
  qvm.vm:
    - name: sd-proxy-buster-template
    - clone:
      - source: whonix-ws-15
      - label: blue
    - tags:
      - add:
        - sd-workstation
        - sd-buster
        - sd-workstation-updates

sd-proxy:
  qvm.vm:
    - name: sd-proxy
    - present:
      - label: blue
    - prefs:
      - template: sd-proxy-buster-template
      - netvm: sd-whonix
      - kernelopts: "nopat apparmor=1 security=apparmor"
      - autostart: true
    - tags:
      - add:
        - sd-workstation
        - sd-buster
    - require:
      - qvm: sd-whonix
      - qvm: sd-proxy-template

# Permit the SecureDrop Proxy to manage Client connections
sd-proxy-dom0-securedrop.Proxy:
  file.prepend:
    - name: /etc/qubes-rpc/policy/securedrop.Proxy
    - text: |
        sd-app sd-proxy allow
        @anyvm @anyvm deny
