# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :


# Installs a Debian 13 (Trixie)-based "sd-admin" VM.
dom0-install-debian-13-template:
  qvm.template_installed:
    - name: debian-13-minimal

# N.B. hardcoding "trixie" rather than reading from sdvars to decouple
# the sd-admin config from the rest of the SDW config during prototyping.
sd-admin-debian-13:
  qvm.vm:
    - name: sd-admin-debian-13
    - clone:
      - source: debian-13-minimal
      - label: red
    - tags:
      - add:
        - sd-workstation
        - sd-workstation-trixie
        - sd-admin
    - require:
      - qvm: dom0-install-debian-13-template

# add fpf repo and grsec package before switching to PVH mode
# TODO: find a less hacky way to do this without an intermediate template
add_template_packages:
  cmd.run:
    - name: 'qubesctl --skip-dom0 --targets=sd-admin-debian-13 state.apply sd-admin-packages'
    - runas: root
    - require:
      - qvm: sd-admin-debian-13

update_template_virtmode:
  qvm-prefs:
    - name: sd-admin-debian-13
    - virt-mode: pvh
    - kernel: 'pvgrub2-pvh'
    - require:
      - cmd: add_template_packages
