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

# Imports "sdvars" for environment config
{% from 'sd-default-config.sls' import sdvars with context %}

include:
  - securedrop_salt.sd-workstation-template
  - securedrop_salt.sd-upgrade-templates

sd-viewer:
  qvm.vm:
    - name: sd-viewer
    - present:
      - template: sd-large-{{ sdvars.distribution }}-template
      - label: green
    - prefs:
      - template: sd-large-{{ sdvars.distribution }}-template
      - netvm: ""
      - template_for_dispvms: True
      - default_dispvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-viewer-vm
        - sd-{{ sdvars.distribution }}
    - features:
      - enable:
        - service.paxctld
    - require:
      - qvm: sd-large-{{ sdvars.distribution }}-template

sd-viewer-default-dispvm:
  cmd.run:
    - name: qubes-prefs default_dispvm sd-viewer
    - require:
      - qvm: sd-viewer
