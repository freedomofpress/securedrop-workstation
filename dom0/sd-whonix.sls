# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.sd-whonix
# ==============
#
# Installs 'sd-whonix' ProxyVM for securedrop journalist workstation.
#
##

include:
  - qvm.template-whonix-gw
  - qvm.sys-firewall

# Temporary workaround to bootstrap Salt support on target.
sd-whonix-install-python-futures:
  cmd.run:
    - name: >
        qvm-run -a whonix-gw-14
        "python -c 'import concurrent.futures' ||
        { sudo apt-get update && sudo apt-get install -qq python-futures ; }" &&
        qvm-shutdown --wait whonix-gw-14

sd-whonix-template:
  qvm.vm:
    - name: sd-whonix-template
    - clone:
      - source: whonix-gw-14
      - label: purple
    - require:
      - pkg: qubes-template-whonix-gw-14
      - qvm: sys-firewall

sd-whonix:
  qvm.vm:
    - name: sd-whonix
    - present:
      - template: sd-whonix-template
      - label: purple
      - mem: 500
    - prefs:
      - provides-network: true
      - netvm: "sys-firewall"
      - autostart: true
    - require:
      - pkg: qubes-template-whonix-gw-14
      - qvm: sys-firewall
      - cmd: sd-whonix-install-python-futures
