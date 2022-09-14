# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-mime-handling
# =====================
#
# Overrides mimetype handling for certain VMs. Instead of relying on the
# /usr/share/applications (system volume), we instead use /home/user/.local/share/
# (private volume). The various mimeapps.list files linked are provided by the
# securedrop-workstation-config package in /opt/, and are symlinked in their
# respective AppVMs by calling the mimeapps-macro with the correct symlink target.
##

sd-private-volume-mimeapps-config-dir:
  file.directory:
    - name: /home/user/.local/share/applications
    - user: user
    - group: user
    - makedirs: True
    - mode: "0755"

sd-private-volume-mailcap-handling:
  file.symlink:
    - name: /home/user/.mailcap
    - target: /opt/sdw/mailcap.default
    - user: user
    - group: user
