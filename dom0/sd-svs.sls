# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.work
# ========
#
# Installs 'sd-svs' AppVM, to persistently store SD data
# This VM has no network configured.
##

sd-svs-template:
  qvm.vm:
    - name: sd-svs-template
    - clone:
      - source: debian-9
      - label: yellow

sd-svs:
  qvm.vm:
    - name: sd-svs
    - present:
      - template: sd-svs-template
      - label: yellow
    - prefs:
      - netvm: ""
  require:
    - qvm: sd-svs-template

sd-svs-dom0-qubes.OpenInVM:
  file.prepend:
    - name: /etc/qubes-rpc/policy/qubes.OpenInVM
    - text: "sd-svs $dispvm:sd-svs-disp allow\n"

# Allow sd-svs to access gpg keys on sd-gpg
sd-svs-dom0-qubes.qubesGpg:
  file.prepend:
    - name: /etc/qubes-rpc/policy/qubes.Gpg
    - text: "sd-svs sd-gpg allow\n"

# Ensure the Qubes menu is populated with relevant app entries,
# so that Nautilus/Files can be started via GUI interactions.
sd-svs-template-sync-appmenus:
  cmd.run:
    - name: >
        qvm-start sd-svs-template &&
        qvm-sync-appmenus sd-svs-template &&
        qvm-shutdown sd-svs-template
