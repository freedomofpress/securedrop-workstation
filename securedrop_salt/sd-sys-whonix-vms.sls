# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Install latest Whonix template, configure apparmor on installed templates,
# and ensure sys-whonix and anon-whonix use latest version.
##

{%- import "qvm/whonix.jinja" as whonix -%}
{% set whonix_version = salt['pillar.get']('qvm:whonix:version', whonix.whonix_version) %}

include:
  - qvm.anon-whonix
  - qvm.sys-whonix
  - qvm.template-whonix-workstation
  - qvm.template-whonix-gateway

# Configure or upgrade sys-whonix and anon-whonix
{% for (vm, component) in [('sys-whonix', 'gateway'), ('anon-whonix', 'workstation')] %}

# Enable apparmor on workstation and gateway templates. The requisite
# does all the work, so in theory, the next two states could be covered
# by a single `qvm.vm` state, but to avoid possible bugs and guarantee
# we are configuring the template, explicitly require qvm.template_installed
# with the expected template name.
whonix-{{ component }}-{{ whonix_version }}-installed:
  qvm.template_installed:
    - name: whonix-{{ component }}-{{ whonix_version }}
    - fromrepo: {{ whonix.whonix_repo }}
    - require:
      - sls: qvm.template-whonix-{{ component }}

whonix-{{ component }}-{{ whonix_version }}-apparmor:
  qvm.vm:
    - name: whonix-{{ component }}-{{ whonix_version }}
    - prefs:
      - kernelopts: "apparmor=1 security=apparmor"
    - require:
      - qvm: whonix-{{ component }}-{{ whonix_version }}-installed

# The Qubes logic is too polite about enforcing template
# settings, using "present" rather than "prefs". Below we
# force the template updates.
poweroff-{{ vm }}:
  qvm.shutdown:
    - name: {{ vm }}
    - flags:
      - force
      - wait
    - onlyif:
      - qvm-check --quiet {{ vm }}
    - unless:
      - qvm-prefs {{ vm }} template | grep -q whonix-{{ component }}-{{ whonix_version }}

# cmd.run is used instead of qvm.vm to avoid a recursive
# requisite issue via the "name" parameter of qvm.vm.
{{ vm }}-upgrade-template:
  cmd.run:
    - name: qvm-prefs {{ vm }} template whonix-{{ component }}-{{ whonix_version }}
    - require:
      - qvm: poweroff-{{ vm }}
      - qvm: whonix-{{ component }}-{{ whonix_version }}-apparmor
      - sls: qvm.{{ vm }}
    - unless:
      - qvm-prefs {{ vm }} template | grep -q whonix-{{ component }}-{{ whonix_version }}

{% endfor %}
