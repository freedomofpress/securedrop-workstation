# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.work
# ========
#
# Installs 'sd-proxy-template' TemplateVM, for hosting the
# securedrop proxy connection and feedback tooling.
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
  require:
    - pkg: qubes-template-whonix-ws-14
    - qvm: sd-whonix

# Ensure the Qubes menu is populated with relevant app entries,
# so that Tor Browser can be started via GUI interactions.
sd-proxy-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start --skip-if-running sd-proxy-template &&
        qvm-sync-appmenus sd-proxy-template &&
        qvm-shutdown sd-proxy-template
