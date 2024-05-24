# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :


# Make sure the "prepare" step has run first, otherwise there's
# a race between migration and removal.
include:
  - sd-upgrade-templates
  - sd-log
  - sd-devices
  - sd-gpg
  - sd-proxy
  - sd-viewer
  - sd-app

run-remove-upgrade-scripts:
  cmd.script:
    - name: salt://securedrop-handle-upgrade
    - args: remove
    - require:
      - sls: sd-upgrade-templates
      - sls: sd-log
      - sls: sd-devices
      - sls: sd-gpg
      - sls: sd-proxy
      - sls: sd-viewer
      - sls: sd-app
