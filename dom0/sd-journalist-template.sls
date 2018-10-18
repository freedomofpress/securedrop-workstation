# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.work
# ========
#
# Installs 'sd-journalist-template' TemplateVM, for hosting the
# securedrop proxy connection and feedback tooling.
#
##

include:
  - qvm.template-whonix-ws
  - sd-whonix

sd-journalist-template:
  qvm.vm:
    - name: sd-journalist-template
    - clone:
      - source: whonix-ws-14
      - label: blue
  require:
    - pkg: qubes-template-whonix-ws-14
    - qvm: sd-whonix

# Ensure the Qubes menu is populated with relevant app entries,
# so that Tor Browser can be started via GUI interactions.
sd-journalist-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start --skip-if-running sd-journalist-template &&
        qvm-sync-appmenus sd-journalist-template &&
        qvm-shutdown sd-journalist-template
