# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Install latest Whonix template, configure apparmor on installed templates,
# and ensure sys-whonix and anon-whonix use latest version.
##

# https://github.com/saltstack/salt/issues/5667

include:
  - qvm.anon-whonix
  - qvm.sys-whonix
  - qvm.template-whonix-gateway
  - qvm.template-whonix-workstation

{% set sd_supported_whonix_version = '17' %}

dom0-shut-down-whonix-stack:
  cmd.run:
    - name: qvm-shutdown --force --wait sys-whonix anon-whonix
    - order: 1

dom0-enabled-apparmor-on-whonix-gw-template:
  qvm.vm:
    - name: whonix-gateway-{{ sd_supported_whonix_version }}
    - prefs:
      - kernelopts: "apparmor=1 security=apparmor"
    - require:
      - qvm: template-whonix-gateway

dom0-enabled-apparmor-on-whonix-ws-template:
  qvm.vm:
    - name: whonix-workstation-{{ sd_supported_whonix_version }}
    - prefs:
      - kernelopts: "apparmor=1 security=apparmor"
    - require:
      - qvm: template-whonix-workstation

# The Qubes logic is too polite about enforcing template
# settings, using "present" rather than "prefs". Below
# we force the template updates.
extend:
  anon-whonix:
    - prefs:
      - template: whonix-workstation-{{ sd_supported_whonix_version }}

  sys-whonix:
    - prefs:
      - template: whonix-gateway-{{ sd_supported_whonix_version }}
