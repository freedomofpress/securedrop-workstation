# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-admin-usb
# ========
#
# Sets up networkless DispVM so administrators can provision USB devices.
#
#

{% import_json "admin_salt/config.json" as d %}

include:
  - admin_salt.sd-admin-template

sd-admin-usb-dvm:
  qvm.vm:
    - name: sd-admin-usb-dvm
    - present:
      # Sets attributes if creating VM for the first time,
      # otherwise `prefs` must be used.
      # Label color is set during initial configuration but
      # not enforced on every Salt run, in case of user customization.
      - label: red
      - template: sd-admin-debian-13
    - prefs:
      - template: sd-admin-debian-13
      - netvm: ""
      - template_for_dispvms: True
      - default_dispvm: ""
      - virt-mode: pvh
      - kernel: "pvgrub2-pvh"
    - features:
      - enable:
        - service.paxctld
      - set:
        {% if d.environment == "prod" %}
        - internal: 1
        {% else %}
        - internal: ""
        {% endif %}
    - tags:
      - add:
        - sd-workstation
        - sd-admin
    - require:
      - qvm: sd-admin-debian-13

sd-admin-usb:
  qvm.vm:
    - name: sd-admin-usb
    - present:
      - label: red
      - template: sd-admin-usb-dvm
      - class: DispVM
    - prefs:
      - template: sd-admin-usb-dvm
      - netvm: ""
      - default_dispvm: ""
      - virt-mode: pvh
      - kernel: "pvgrub2-pvh"
    - features:
      - enable:
        - service.paxctld
      - set:
        - menu-items: >-
            org.gnome.Nautilus.desktop
            org.gnome.DiskUtility.desktop
    - tags:
      - add:
        - sd-workstation
        - sd-admin
    - require:
      - qvm: sd-admin-usb-dvm
