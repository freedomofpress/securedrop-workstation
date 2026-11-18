# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Removes previous udev configurations in a USB Qube
##

# If sys-usb is disposable, we have already set up sd-{supported-fedora-version}-dvm to make our
# modifications in, so we only want to modify sys-usb if it is a regular AppVM

{% set apply = True %}
{% if grains['id'] == 'sys-usb' and salt['pillar.get']('qvm:sys-usb:disposable', true) %}
  {% set apply = False %}
{% endif %}

{% if apply %}
sd-clear-udev-rules:
  file.absent:
    - names:
      - /rw/config/sd/etc/udev/rules.d/99-sd-devices.rules
      - /etc/udev/rules.d/99-sd-devices.rules
      - /usr/local/bin/sd-attach-export-device

sd-clear-rc-local-udev-rules:
  file.replace:
    - name: /rw/config/rc.local
    # Remove the whole block, including the markers
    - pattern: '(?s)### BEGIN securedrop-workstation ###.*?### END securedrop-workstation ###\n?'
    - repl: ''
    - bufsize: file
    - ignore_if_missing: True

sd-udev-reload:
  cmd.run:
    - name: udevadm control --reload
    - require:
      - file: sd-clear-udev-rules
{% endif %}
