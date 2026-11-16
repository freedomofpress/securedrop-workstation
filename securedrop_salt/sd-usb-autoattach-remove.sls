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
  file.blockreplace:
    - name: /rw/config/rc.local
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: ''
    - onlyif: grep -qsxF '### BEGIN securedrop-workstation ###' /rw/config/rc.local

sd-udev-reload:
  cmd.run:
    - name: udevadm control --reload
    - require:
      - file: sd-clear-udev-rules
{% endif %}
