# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-svs-disp
# ========
#
# Configures the 'sd-svs-disp' template VM, which will be used as the
# base dispvm for the SVS vm (will be used to open all submissions
# after processing).
# This VM has no network configured.
##

include:
  - sd-workstation-template

sd-svs-disp-template:
  qvm.vm:
    - name: sd-svs-disp-buster-template
    - clone:
      - source: securedrop-workstation-buster
      - label: green
    - require:
      - sls: sd-workstation-template
      - sls: sd-upgrade-templates

sd-svs-disp:
  qvm.vm:
    - name: sd-svs-disp
    - present:
      - template: sd-svs-disp-buster-template
      - label: green
    - prefs:
      - template: sd-svs-disp-buster-template
      - netvm: ""
      - template_for_dispvms: True
    - tags:
      - add:
        - sd-workstation
        - sd-svs-disp-vm
        - buster
    - features:
      - enable:
        - service.paxctld
    - require:
      - qvm: sd-svs-disp-buster-template

sd-svs-disp-default-dispvm:
  cmd.run:
    - name: qubes-prefs default_dispvm sd-svs-disp
    - require:
      - qvm: sd-svs-disp
