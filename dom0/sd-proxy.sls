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
  - sd-templates

sd-proxy:
  qvm.vm:
    - name: sd-proxy
    - present:
      - label: blue
    - prefs:
      - template: sd-small-buster-template
      - netvm: sd-whonix
      - autostart: true
    - tags:
      - add:
        - sd-workstation
        - sd-buster
    - require:
      - qvm: sd-whonix
      - qvm: sd-small-buster-template

# Permit the SecureDrop Proxy to manage Client connections
sd-proxy-dom0-securedrop.Proxy:
  file.prepend:
    - name: /etc/qubes-rpc/policy/securedrop.Proxy
    - text: |
        sd-app sd-proxy allow
        @anyvm @anyvm deny
