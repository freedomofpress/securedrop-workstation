# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-export-files
# ========
#
# Moves files into place on sd-export
#
##
include:
  - fpf-apt-test-repo

# Libreoffice needs to be installed here to convert to pdf to allow printing
sd-export-install-libreoffice:
  pkg.installed:
    - name: libreoffice
    - retry:
        attempts: 3
        interval: 60
    - install_recommends: False

# Install securedrop-export package https://github.com/freedomofpress/securedrop-export
sd-export-install-package:
  pkg.installed:
    - name: securedrop-export

# populate sd-export-config.json in sd-export-template. This contains the usb
# device information used for the export

{% import_json "sd/config.json" as d %}

install-securedrop-export-json-config:
  file.managed:
    - name: /etc/sd-export-config.json
    - source: salt://sd/sd-export/config.json.j2
    - template: jinja
    - context:
        # get pci ID and usb ID from config.json
        pci_bus_id_value: {{ (d.usb.device | regex_search('sys-usb:(.)-.'))[0] | int }}
        usb_device_value: {{ (d.usb.device | regex_search('sys-usb:.-(.)'))[0] | int }}
    - user: user
    - group: user
    - mode: 0644
    - makedirs: True
