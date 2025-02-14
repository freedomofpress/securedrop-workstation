# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Install latest Whonix template, configure apparmor on installed templates,
# and ensure sys-whonix and anon-whonix use latest version.
##

{% set whonix_version = salt['pillar.get']('qvm:whonix:version', '17') %}

include:
  - qvm.anon-whonix
  - qvm.sys-whonix
  - qvm.template-whonix-gateway
  - qvm.template-whonix-workstation

# If sys-whonix or anon-whonix VMs are using an outdated template,
# upgrade them. If VMs are absent, configure them.

{% for vm in ['sys-whonix', 'anon-whonix'] %}

poweroff-{{ vm }}:
  qvm.shutdown:
    - name: {{ vm }}
    - flags:
      - force
      - wait
    - onlyif:
      - qvm-check --quiet {{ vm }} 
    - require:
      - qvm: {{ vm }}-present
 
{{ vm }}-present:
  qvm.vm:
    - name: {{ vm }}
    - require:
      - sls: qvm.template-whonix-workstation
      - sls: qvm.template-whonix-gateway

{% endfor %}

# Enable apparmor on workstation and gateway templates
# by extending the upstream template configuration states
extend:
  whonix-workstation-tag:
    qvm.vm:
      - prefs:
        - kernelopts: "apparmor=1 security=apparmor"

  whonix-gateway-tag:
    qvm.vm:
      - prefs:
        - kernelopts: "apparmor=1 security=apparmor"

# The Qubes logic is too polite about enforcing template
# settings, using "present" rather than "prefs". Below we
# force the template updates by extending the upstream states,
# which will also create the VMs if they are missing.
  sys-whonix:
    qvm.vm:
      - prefs:
        - template: whonix-gateway-{{ whonix_version }}

  anon-whonix:
    qvm.vm:
      - prefs:
        - template: whonix-workstation-{{ whonix_version }}
