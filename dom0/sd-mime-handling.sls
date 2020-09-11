# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-mime-handling
# =====================
#
# Overrides mimetype handling for certain VMs. Instead of relying on the
# /usr/share/applications (system volume), we instead use /home/user/.local/share/
# (private volume). The various mimeapps.list files linked are provided by the
# securedrop-workstation-config package in /opt/, and are symlinked here in their
# respective AppVMs.
##

sd-private-volume-mimeapps-config-dir:
  file.directory:
    - name: /home/user/.local/share/applications
    - user: user
    - group: user
    - makedirs: True
    - mode: "0755"

{% if grains['id'] in ["sd-viewer", "sd-app", "sd-devices-dvm"] %}

sd-private-volume-mimeapps-handling:
  file.symlink:
    - name: /home/user/.local/share/applications/mimeapps.list
    - target: /opt/sdw/mimeapps.list.{{ grains['id'] }}
    - user: user
    - group: user
    - require:
      - file: sd-private-volume-mimeapps-config-dir

{% else %}

sd-private-volume-mimeapps-handling:
  file.symlink:
    - name: /home/user/.local/share/applications/mimeapps.list
    - target: /opt/sdw/mimeapps.list.default
    - user: user
    - group: user
    - require:
      - file: sd-private-volume-mimeapps-config-dir

{% endif %}
