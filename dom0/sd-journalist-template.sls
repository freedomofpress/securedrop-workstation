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
  - sd-dom0-files
  - sd-whonix

sd-journalist-template:
  qvm.vm:
    - name: sd-journalist-template
    - clone:
      - source: whonix-ws-14
      - label: blue
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: sd-whonix
      - sls: sd-dom0-files
      - qvm: sd-workstation-template

# Ensure the Qubes menu is populated with relevant app entries,
# so that Tor Browser can be started via GUI interactions.
sd-journalist-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start --skip-if-running sd-journalist-template &&
        qvm-sync-appmenus sd-journalist-template &&
        qvm-shutdown --wait sd-journalist-template
    - require:
      - qvm: sd-journalist-template
