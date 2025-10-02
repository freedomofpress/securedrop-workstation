# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# NOTE: this file may be removed after Qubes 4.2 is EOL (Whonix 17 assumed non-existent)

# Disable apparmor on workstation and gateway templates. Originally Whonix
# shipped without kernel parameters. This reverts a previous workstation change
# that added AppArmor

{% for (vm, component) in [('sys-whonix', 'gateway'), ('anon-whonix', 'workstation')] %}
whonix-{{ component }}-17-remove-apparmor:
  qvm.vm:
    - name: whonix-{{ component }}-17
    - prefs:
      - kernelopts: "*default*"
    - onlyif:
      - qvm-check --quiet {{ vm }}
{% endfor %}
