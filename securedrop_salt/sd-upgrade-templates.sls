# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# Prepare for a template migration by shutting down or removing AppVMs using
# older template versions. In the absence of older templates, this should be a
# noop.
# TODO: a script that checked for pre-consolidation templates and dropped a
# migration flag for sdw-admin --apply was run as a prerequisite here. This was
# intended to account for situations where a migration was required but a flag
# would not be present in the latest dom-config RPM (IE the system had the old
# templates but had skipped the RPM update where the new templates were introduced.)
# A simpler method of detecting when base templates change is required.

run-prep-upgrade-scripts:
  cmd.script:
    - name: salt://securedrop_salt/securedrop-handle-upgrade
    - args: prepare
