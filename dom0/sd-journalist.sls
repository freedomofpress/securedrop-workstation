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
  - sd-dom0-files

sd-journalist:
  qvm.vm:
    - name: sd-journalist
    - present:
      - template: sd-journalist-template
      - label: blue
    - prefs:
      - netvm: sd-whonix
      - kernelopts: "nopat apparmor=1 security=apparmor"
    - tags:
      - add:
        - sd-workstation
    - require:
      - qvm: sd-whonix
      - qvm: sd-journalist-template
      - sls: sd-dom0-files

# Permit the SecureDrop Proxy to manage Client connections
sd-journalist-dom0-securedrop.Proxy:
  file.prepend:
    - name: /etc/qubes-rpc/policy/securedrop.Proxy
    - text: |
        sd-svs sd-journalist allow
        $anyvm $anyvm deny
