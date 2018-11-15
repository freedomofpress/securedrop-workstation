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
  - qvm.template-whonix-ws
  - sd-whonix

sd-proxy-template:
  qvm.vm:
    - name: sd-proxy-template
    - clone:
      - source: whonix-ws-14
      - label: blue
    - tags:
      - add:
        - sd-workstation

sd-proxy:
  qvm.vm:
    - name: sd-proxy
    - present:
      - template: sd-proxy-template
      - label: blue
    - prefs:
      - netvm: sd-whonix
      - kernelopts: "nopat apparmor=1 security=apparmor"
    - tags:
      - add:
        - sd-workstation
    - require:
      - pkg: qubes-template-whonix-ws-14
      - qvm: sd-whonix
      - qvm: sd-proxy-template

# Permit the SecureDrop Proxy to manage Client connections
sd-proxy-dom0-securedrop.Proxy:
  file.prepend:
    - name: /etc/qubes-rpc/policy/securedrop.Proxy
    - text: |
        sd-svs sd-proxy allow
        $anyvm $anyvm deny
