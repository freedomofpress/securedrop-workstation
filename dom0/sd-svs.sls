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
      - template: debian-9
      - label: yellow
    - prefs:
      - netvm: ""

sd-svs-dom0-qubes.OpenInVM:
  file.prepend:
    - name: /etc/qubes-rpc/policy/qubes.OpenInVM
    - text: "sd-svs $dispvm:sd-svs-disp allow\n"

# Allow sd-svs to access gpg keys on sd-gpg
sd-svs-dom0-qubes.qubesGpg:
  file.prepend:
    - name: /etc/qubes-rpc/policy/qubes.Gpg
    - text: "sd-svs sd-gpg allow\n"
