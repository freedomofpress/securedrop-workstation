# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

#
# Installs consolidated templateVMs:
# - sd-small-buster-template, to be used for
#   sd-app, sd-log, and sd-proxy
# - sd-large-buster-template, to be used for
#   sd-export and sd-viewer
##
include:
  - sd-workstation-template
  - sd-upgrade-templates

sd-small-buster-template:
  qvm.vm:
    - name: sd-small-buster-template
    - clone:
      - source: securedrop-workstation-buster
      - label: red
    - tags:
      - add:
        - sd-workstation
        - sd-buster
        - sd-workstation-updates
    - require:
      - sls: sd-workstation-template
      - sls: sd-upgrade-templates

sd-large-buster-template:
  qvm.vm:
    - name: sd-large-buster-template
    - clone:
      - source: securedrop-workstation-buster
      - label: red
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: sd-workstation-template

