# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

include:
  - sd-upgrade-templates

# The Qubes logic is too polite about enforcing template
# settings, using "present" rather than "prefs". Below
# we force the template updates.
sys-whonix-template-config:
  qvm.vm:
    - name: sys-whonix
    - prefs:
      - template: whonix-gateway-17
    - require:
      - sls: sd-upgrade-templates

anon-whonix-template-config:
  qvm.vm:
    - name: anon-whonix
    - prefs:
      - template: whonix-workstation-17
