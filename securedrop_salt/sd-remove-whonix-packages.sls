# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
#  Remove workstation components in whonix-gateway-17
#
#  NOTE: this file should be safe to remove after a few releases. Even if some
#  Workstations miss some updates (due to not being in use for a while), the
#  mere presence of the repo/package, does not affect regular system behavior.
##

sd-cleanup-whonix-gateway:
  cmd.run:
    - names:
      - "sudo apt purge --yes securedrop-keyring securedrop-qubesdb-tools securedrop-whonix-config ||:"
      - "sudo rm -f /etc/apt/sources.list.d/apt_freedom_press.sources ||:"
