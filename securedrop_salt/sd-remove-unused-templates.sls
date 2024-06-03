# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :


# Make sure the "prepare" step has run first, otherwise there's
# a race between migration and removal.
include:
  - securedrop_salt.sd-upgrade-templates
  - securedrop_salt.sd-log
  - securedrop_salt.sd-devices
  - securedrop_salt.sd-gpg
  - securedrop_salt.sd-proxy
  - securedrop_salt.sd-viewer
  - securedrop_salt.sd-app

run-remove-upgrade-scripts:
  cmd.script:
    - name: salt://securedrop_salt/securedrop-handle-upgrade
    - args: remove
    - require:
      - sls: securedrop_salt.sd-upgrade-templates
      - sls: securedrop_salt.sd-log
      - sls: securedrop_salt.sd-devices
      - sls: securedrop_salt.sd-gpg
      - sls: securedrop_salt.sd-proxy
      - sls: securedrop_salt.sd-viewer
      - sls: securedrop_salt.sd-app
