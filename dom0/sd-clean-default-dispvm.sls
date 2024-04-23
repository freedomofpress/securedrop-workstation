# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

set-fedora-as-default-dispvm:
  cmd.run:
    - name: qvm-check fedora-39-dvm && qubes-prefs default_dispvm fedora-39-dvm || qubes-prefs default_dispvm ''
