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

sd-proxy-template:
  qvm.vm:
    - name: sd-proxy-template
    - clone:
      - source: sd-workstation-template
      - label: blue
    - tags:
      - add:
        - sd-workstation
