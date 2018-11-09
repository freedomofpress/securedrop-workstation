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

sd-workstation-template:
  qvm.vm:
    - name: sd-workstation-template
    - clone:
      - source: debian-9
      - label: yellow
    - prefs:
      - virt-mode: hvm
      - kernel: ''
    - tags:
      - add:
        - sd-workstation
    - require:
      - sls: sd-dom0-files
