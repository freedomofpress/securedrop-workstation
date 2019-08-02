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

sd-export-template-install-packages:
  pkg.installed:
    - pkgs:
      - cryptsetup
      - cups
      - task-print-server
      - system-config-printer
      - xpp
      - libcups2-dev
      - python3-dev
      - libtool-bin
      - unoconv

# Libreoffice needs to be installed here to convert to pdf to allow printing
sd-export-install-libreoffice:
  pkg.installed:
    - name: libreoffice
    - retry:
        attempts: 3
        interval: 60
    - install_recommends: False

sd-export-send-to-usb-script:
  file.managed:
    - name: /usr/bin/send-to-usb
    - source: salt://sd/sd-export/send-to-usb
    - user: root
    - group: root
    - mode: 755
    - makedirs: True

sd-export-desktop-file:
  file.managed:
    - name: /usr/share/applications/send-to-usb.desktop
    - source: salt://sd/sd-export/send-to-usb.desktop
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
  cmd.run:
    - name: sudo update-desktop-database /usr/share/applications
    - require:
      - file: sd-export-desktop-file

sd-export-file-format:
  file.managed:
    - name: /usr/share/mime/packages/application-x-sd-export.xml
    - source: salt://sd/sd-export/application-x-sd-export.xml
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
  cmd.run:
    - name: sudo update-mime-database /usr/share/mime
    - require:
      - file: sd-export-file-format
      - file: sd-export-desktop-file

sd-export-securedrop-icon:
  file.managed:
    - name: /usr/share/securedrop/icons/sd-logo.png
    - source: salt://sd/sd-proxy/logo-small.png
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

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
