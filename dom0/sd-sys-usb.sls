# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Installs udev configuration in sys-usb for automatically attaching
# USB devices to sd-devices.
##

sd-udev-rules:
  file.managed:
    - name: /rw/config/sd/etc/udev/rules.d/99-sd-devices.rules
    - source: salt://sd/sys-usb/99-sd-devices.rules
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
    - source: salt://sd/sys-usb/sd-attach-export-device
    - user: root
    - group: root
    - mode: 0555
