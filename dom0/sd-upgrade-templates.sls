# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# If the entire config must be reapplied, the "check-migration" script
# will drop a flag on disk in dom0 that the GUI updater will find,
# conditionally enabling a longer run.
determine-whether-migration-required:
  cmd.script:
    - name: salt://securedrop-check-migration

run-prep-upgrade-scripts:
  cmd.script:
    - name: salt://securedrop-handle-upgrade
    - args: prepare
    - require:
      - cmd: determine-whether-migration-required
