# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Install latest Whonix template, configure apparmor on installed templates,
# and ensure sys-whonix and anon-whonix use latest version.
##

include:
  - qvm.anon-whonix

{% set sd_supported_whonix_version = '17' %}

dom0-enabled-apparmor-on-whonix-gw-template:
  qvm.vm:
    - name: whonix-gateway-{{ sd_supported_whonix_version }}
    - prefs:
      - kernelopts: "apparmor=1 security=apparmor"
    - require:
      - qvm: anon-whonix

dom0-enabled-apparmor-on-whonix-ws-template:
  qvm.vm:
    - name: whonix-workstation-{{ sd_supported_whonix_version }}
    - prefs:
      - kernelopts: "apparmor=1 security=apparmor"
    - require:
      - qvm: anon-whonix

sys-whonix-poweroff:
  # Shut down in order to apply template changes
  qvm.shutdown:
    - name: sys-whonix
    - flags:
      - force
      - wait
    - require:
      - qvm: dom0-enabled-apparmor-on-whonix-gw-template

anon-whonix-poweroff:
  # Shut down in order to apply template changes
  qvm.shutdown:
    - name: anon-whonix
    - flags:
      - force
      - wait
    - require:
      - qvm: dom0-enabled-apparmor-on-whonix-ws-template

# The Qubes logic is too polite about enforcing template
# settings, using "present" rather than "prefs". Below
# we force the template updates.
sys-whonix-template-config:
  qvm.vm:
    - name: sys-whonix
    - prefs:
      - template: whonix-gateway-{{ sd_supported_whonix_version }}
    - require:
      - qvm: sys-whonix-poweroff

anon-whonix-template-config:
  qvm.vm:
    - name: anon-whonix
    - prefs:
      - template: whonix-workstation-{{ sd_supported_whonix_version }}
    - require:
      - qvm: anon-whonix-poweroff
