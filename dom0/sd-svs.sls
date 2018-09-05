# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.work
# ========
#
# Installs 'sd-svs' AppVM, to persistently store SD data
# This VM has no network configured.
##

sd-svs:
  qvm.vm:
    - name: sd-svs
    - present:
      - template: fedora-28
      - label: yellow
    - prefs:
      - netvm: ""

/etc/qubes-rpc/policy/qubes.OpenInVM:
  file.line:
    - content: sd-svs $dispvm:sd-svs-disp allow
    - mode: insert
    - location: start
