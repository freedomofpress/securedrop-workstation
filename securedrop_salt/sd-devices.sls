# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

#
# Installs 'sd-devices' AppVM, to persistently store SD data
# This VM has no network configured.
##

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}

include:
  - securedrop_salt.sd-workstation-template

sd-devices-dvm:
  qvm.vm:
    - name: sd-devices-dvm
    - present:
      # Sets attributes if creating VM for the first time,
      # otherwise `prefs` must be used.
      # Label color is set during initial configuration but
      # not enforced on every Salt run, in case of user customization.
      - label: red
      - template: sd-large-{{ sdvars.distribution }}-template
    - prefs:
      - template: sd-large-{{ sdvars.distribution }}-template
      - netvm: ""
      - template_for_dispvms: True
      - default_dispvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-{{ sdvars.distribution }}
    - features:
      - enable:
        - service.paxctld
        - service.cups
    - require:
      - qvm: sd-large-{{ sdvars.distribution }}-template

sd-devices-create-named-dispvm:
  qvm.vm:
    - name: sd-devices
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
    - features:
      - enable:
        - service.securedrop-mime-handling
        - service.avahi
      - set:
        - vm-config.SD_MIME_HANDLING: sd-devices
        - menu-items: "org.gnome.Nautilus.desktop org.gnome.DiskUtility.desktop"
    - require:
      - qvm: sd-devices-dvm
