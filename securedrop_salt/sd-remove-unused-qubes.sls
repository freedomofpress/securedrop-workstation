# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :


# WARNING: only remove when complete reinstall is assumed (e.g. 1.0.0 release)
# This is because the workstation may have been offline for a while
# and skipped some salt updates.
{% set qubes_for_removal = [
  "sd-small-bookworm-template",
  "sd-large-bookworm-template",
  "sd-base-bookworm-template",
  "sd-retain-logvm",
  "sd-whonix",
] %}

{% for qube_name in qubes_for_removal %}
poweroff-before-removal-{{ qube_name }}:
  qvm.shutdown:
    - name: {{ qube_name }}
    - flags:
      - force
      - wait
    - onlyif:
      - qvm-check --quiet {{ qube_name }}
    - order: last

remove-{{ qube_name }}:
  qvm.absent:
    - name: {{ qube_name }}
    - require:
      - qvm: poweroff-before-removal-{{ qube_name }}
    - onlyif:
      - qvm-check --quiet {{ qube_name }}
    - order: last

{% endfor %}
