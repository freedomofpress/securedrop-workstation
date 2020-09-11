# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

include:
  - sd-dom0-files

# Sets virt_mode and kernel to use custom hardened kernel.
sd-workstation-template:
  qvm.vm:
    - name: securedrop-workstation-buster
    - prefs:
      - virt-mode: hvm
      - kernel: ''
    - tags:
      - add:
        - sd-workstation
        - sd-buster
        - sd-workstation-updates
    - features:
      - enable:
        - service.paxctld
    - require:
      - pkg: dom0-install-securedrop-workstation-template

# Installs consolidated templateVMs:
# - sd-small-buster-template, to be used for
#   sd-app, sd-gpg, sd-log, and sd-proxy
# - sd-large-buster-template, to be used for
#   sd-export and sd-viewer
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
      - qvm: sd-workstation-template

sd-large-buster-template:
  qvm.vm:
    - name: sd-large-buster-template
    - clone:
      - source: securedrop-workstation-buster
      - label: red
    - tags:
      - add:
        - sd-workstation
        - sd-buster
        - sd-workstation-updates
    - require:
      - qvm: sd-workstation-template
