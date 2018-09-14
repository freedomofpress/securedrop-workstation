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

# Temporary workarounds for sd-journalist:
#
#   * python-futures required bootstrap Salt support
#   * python-qt4 required for sd-process-feedback GUI integration
#
install python-qt4 and python-futures:
  cmd.run:
    - name: qvm-run -a whonix-ws-14 'sudo apt-get update && sudo apt-get install -qq python-futures python-qt4'

# When our Qubes bug is fixed, this will *not* be used
sd-journalist-dom0-qubes.OpenInVM:
  file.prepend:
    - name: /etc/qubes-rpc/policy/qubes.OpenInVM
    - text: "sd-journalist sd-decrypt allow\n"

# Allow sd-journalist to open files in sd-decrypt-bsed dispVM's
# When our Qubes bug is fixed, this will be used.
sd-journalist-dom0-qubes.OpenInVM-disp:
  file.prepend:
    - name: /etc/qubes-rpc/policy/qubes.OpenInVM
    - text: "sd-journalist sd-svs allow\n"
