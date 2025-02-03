# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# Remove VMs not tagged with `sd-workstation` tag.
# 
sd-remove-untagged-vms:
  qvm.absent:
    - name: sd-retain-logvm
    - onlyif:
      - qvm-check --quiet sd-retain-logvm
