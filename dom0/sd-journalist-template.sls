# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-journalist-template
# ========
#
# Package config for template (sd-journalist-whonix-ws) for sd-journalist 
# AppVM
# 
##

# Nautilus is the default file manager in all Fedora based
# VMs so let's use it here too for consistency and since we
# know that Nautilus respects our mimeapps.list settings.
nautilus:
  pkg.installed

# Remove Dolphin in favor of Nautilus.
dolphin:
  pkg.removed

