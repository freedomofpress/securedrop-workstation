# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-viewer
# ========
#
# Configures the 'sd-viewer' template VM, which will be used as the
# base dispvm for the SVS vm (will be used to open all submissions
# after processing).
# This VM has no network configured.
##

include:
  - sd-workstation-template
  - sd-upgrade-templates

sd-viewer-template:
  qvm.vm:
    - name: sd-viewer-buster-template
    - clone:
      - source: securedrop-workstation-buster
      - label: green
    - tags:
      - add:
        - sd-workstation
        - sd-workstation-updates
    - require:
      - sls: sd-workstation-template
      - sls: sd-upgrade-templates

sd-viewer:
  qvm.vm:
    - name: sd-viewer
    - present:
      - template: sd-large-buster-template
      - label: green
    - prefs:
      - template: sd-large-buster-template
      - netvm: ""
      - template_for_dispvms: True
    - tags:
      - add:
        - sd-workstation
        - sd-viewer-vm
        - sd-buster
    - features:
      - enable:
        - service.paxctld
    - require:
      - qvm: sd-large-buster-template

sd-viewer-default-dispvm:
  cmd.run:
    - name: qubes-prefs default_dispvm sd-viewer
    - require:
      - qvm: sd-viewer
