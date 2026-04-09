# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

#
# Creates 'sd-printers' (a disposable qube), a networkless qube dedicated to
# printing exported submissions.
##

include:
  - securedrop_salt.sd-devices

sd-printers-create-named-dispvm:
  qvm.vm:
    - name: sd-printers
    - present:
      # Sets attributes if creating VM for the first time,
      # otherwise `prefs` must be used.
      - label: red
      - template: sd-devices-dvm
      - class: DispVM
    - prefs:
      - template: sd-devices-dvm
      - default_dispvm: ""
      - netvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-export-target
    - features:
      - enable:
        - service.securedrop-mime-handling
        - service.avahi
        - service.cups
      - set:
        - vm-config.SD_MIME_HANDLING: sd-devices  # Same behavior as sd-devices
        - menu-items: ""
    - require:
      - qvm: sd-devices-dvm
