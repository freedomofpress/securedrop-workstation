# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Installs udev configuration in a USB Qube for automatically attaching
# USB devices to sd-devices.
##

# If sys-usb is disposable, we have already set up sd-{supported-fedora-version}-dvm to make our
# modifications in, so we only want to modify sys-usb if it is a regular AppVM

{% set apply = True %}
{% if grains['id'] == 'sys-usb' and salt['pillar.get']('qvm:sys-usb:disposable', true) %}
  {% set apply = False %}
{% endif %}

{% if apply %}
sd-udev-rules:
  file.managed:
    - name: /rw/config/sd/etc/udev/rules.d/99-sd-devices.rules
    - source: salt://securedrop_salt/99-sd-devices.rules
    - user: root
    - group: root
    - mode: 0444
    - makedirs: True

sd-rc-local-udev-rules:
  file.blockreplace:
    - name: /rw/config/rc.local
    - append_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        # Add udev rules for export devices
        ln -sf /rw/config/sd/etc/udev/rules.d/99-sd-devices.rules /etc/udev/rules.d/
        udevadm control --reload
    - require:
      - file: sd-udev-rules
  cmd.run:
    - name: ln -sf /rw/config/sd/etc/udev/rules.d/99-sd-devices.rules /etc/udev/rules.d/ && udevadm control --reload
    - require:
      - file: sd-rc-local-udev-rules

sd-attach-export-device:
  file.managed:
    - name: /usr/local/bin/sd-attach-export-device
    - source: salt://securedrop_salt/sd-attach-export-device
    - user: root
    - group: root
    - mode: 0555
{% endif %}
