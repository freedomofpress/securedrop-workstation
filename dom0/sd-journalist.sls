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
  - qvm.template-whonix-ws
#  - sd-whonix

sd-journalist:
  qvm.vm:
    - name: sd-journalist
    - present:
      - template: whonix-ws-14
      - label: blue
    - prefs:
      - netvm: sd-whonix
    - require:
      - pkg: qubes-template-whonix-ws-14
      - qvm: sd-whonix

/etc/qubes-rpc/policy/sd-process.Feedback:
  file.managed:
    - source: salt://sd/sd-journalist/sd-process.Feedback-dom0
    - user: root
    - group: root
    - mode: 644

# Allow sd-journslist to open files in sd-decrypt
# When our Qubes bug is fixed, this will *not* be used
/etc/qubes-rpc/policy/qubes.OpenInVM:
  file.line:
    - content: sd-journalist sd-decrypt allow
    - mode: insert
    - location: start

# Allow sd-journalist to open files in sd-decrypt-bsed dispVM's
# When our Qubes bug is fixed, this will be used.
/etc/qubes-rpc/policy/qubes.OpenInVM:
  file.line:
    - content: sd-journalist $dispvm:sd-decrypt allow
    - mode: insert
    - location: start
