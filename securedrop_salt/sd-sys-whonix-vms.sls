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

# If sys-whonix or anon-whonix VMs are using an outdated whonix template,
# upgrade them
{% set upgrade_flag = false %}

{% for vm in ['sys-whonix', 'anon-whonix'] %}
{% if not salt['pillar.get']('qvm:' ~ vm ~ ':template', '')|string.endswith(~ whonix_version ~) %}
{% set upgrade_flag = true %}
poweroff-{{ vm }}:
  qvm.shutdown:
    - name: {{ vm }}
    - flags:
      - force
      - wait
    - require:
      - qvm: {{ vm }}-exists

{{ vm }}-exists:
  qvm.vm:
    - name: {{ vm }}
    - require:
      - qvm.template-whonix-workstation
      - qvm.template-whonix-gateway

{% endfor %}

# Enable apparmor on workstation and gateway templates
# by extending the upstream qvm.vm configuration state
extend:
  qvm.whonix-workstation-tag:
    - prefs:
      - kernelopts: "apparmor=1 security=apparmor"

  qvm.whonix-gateway-tag:
    - prefs:
      - kernelopts: "apparmor=1 security=apparmor"

{% if upgrade_flag %}
The Qubes logic is too polite about enforcing template
# settings, using "present" rather than "prefs". Below
# we force the template updates. 
  qvm.sys-whonix:
    - prefs:
      - template: whonix-gateway-{{ whonix_version }}

  qvm.anon-whonix:
    - prefs:
      - template: whonix-workstation-{{ whonix_version }}
{% endif %}