# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

include:
  # Import the upstream Qubes-maintained anon-whonix settings.
  # The anon-whonix config pulls in sys-whonix and sys-firewall,
  # as well as ensures the latest versions of Whonix are installed.
  - qvm.anon-whonix
  - sd-upgrade-templates

# The Qubes logic is too polite about enforcing template
# settings, using "present" rather than "prefs". Below
# we force the template updates.
sys-whonix-template-config:
  qvm.vm:
    - name: sys-whonix
    - prefs:
      - template: whonix-gw-15
    - require:
      - sls: qvm.anon-whonix
      - sls: sd-upgrade-templates

anon-whonix-template-config:
  qvm.vm:
    - name: anon-whonix
    - prefs:
      - template: whonix-ws-15
    - require:
      - sls: qvm.anon-whonix
