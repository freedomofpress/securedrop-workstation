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
  - sd-journalist-template

sd-journalist:
  qvm.vm:
    - name: sd-journalist
    - present:
      - template: sd-journalist-template
      - label: blue
    - prefs:
      - netvm: sd-whonix
      - kernelopts: "nopat apparmor=1 security=apparmor"
    - tags:
      - add:
        - sd-workstation
    - require:
      - pkg: qubes-template-whonix-ws-14
      - qvm: sd-whonix
      - qvm: sd-journalist-template
      - cmd: sd-journalist-install-python-futures

# Temporary workarounds for sd-journalist:
#
#   * python-futures required bootstrap Salt support
#   * python-qt4 required for GUI window to inform people not to take actions in this VM
#
sd-journalist-install-python-futures:
  cmd.run:
    - name: >
        qvm-run -a whonix-ws-14
        "python -c 'import concurrent.futures' ||
        { sudo apt-get update && sudo apt-get install -qq python-futures ; }" &&
        qvm-shutdown --wait whonix-ws-14

# Permit the SecureDrop Proxy to manage Client connections
sd-journalist-dom0-securedrop.Proxy:
  file.prepend:
    - name: /etc/qubes-rpc/policy/securedrop.Proxy
    - text: |
        sd-svs sd-journalist allow
        $anyvm $anyvm deny
