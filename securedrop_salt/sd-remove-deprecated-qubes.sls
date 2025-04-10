# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :


# WARNING: only remove when complete reinstall is assumed (e.g. 1.0.0 release)
# This is because the workstation may have been offline for a while
# and skipped some salt updates.
{% for untagged_qube in ["sd-retain-logvm"] %}

poweroff-before-removal-{{ untagged_qube }}:
  qvm.shutdown:
    - name: {{ untagged_qube }}
    - flags:
      - force
      - wait
    - onlyif:
      - qvm-check --quiet {{ untagged_qube }}
    - order: last

remove-{{ untagged_qube }}:
  qvm.absent:
    - name: {{ untagged_qube }}
    - require:
      - qvm: poweroff-before-removal-{{ untagged_qube }}
    - onlyif:
      - qvm-check --quiet {{ untagged_qube }}
    - order: last

{% endfor %}
