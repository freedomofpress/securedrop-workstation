# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

include:
  - sd-dom0-files

# Sets virt_mode and kernel to use custom hardened kernel.
sd-workstation-template:
  qvm.vm:
    - name: securedrop-workstation
    - prefs:
      - virt-mode: hvm
      - kernel: ''
    - tags:
      - add:
        - sd-workstation
    - require:
      - pkg: dom0-install-securedrop-workstation-template
