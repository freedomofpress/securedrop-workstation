# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# Imports "sdvars" for environment config
{% from 'sd-default-config.sls' import sdvars with context %}

include:
  - sd-dom0-files

# Installs consolidated templateVMs:
# Sets virt_mode and kernel to use custom hardened kernel.
# - sd-small-{{ sdvars.distribution }}-template, to be used for
#   sd-app, sd-gpg, sd-log, and sd-proxy
# - sd-large-{{ sdvars.distribution }}-template, to be used for
#   sd-export and sd-viewer
sd-small-{{ sdvars.distribution }}-template:
  qvm.vm:
    - name: sd-small-{{ sdvars.distribution }}-template
    - clone:
      - source: debian-12-minimal
      - label: red
    - prefs:
      - virt-mode: pvh
      - kernel: 'pvgrub2-pvh'
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - features:
      - enable:
        - service.paxctld
    - require:
      - cmd: dom0-install-debian-base-template

sd-large-{{ sdvars.distribution }}-template:
  qvm.vm:
    - name: sd-large-{{ sdvars.distribution }}-template
    - clone:
      - source: debian-12-minimal
      - label: red
    - prefs:
      - virt-mode: pvh
      - kernel: 'pvgrub2-pvh'
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - features:
      - enable:
        - service.paxctld
    - require:
      - cmd: dom0-install-debian-base-template
