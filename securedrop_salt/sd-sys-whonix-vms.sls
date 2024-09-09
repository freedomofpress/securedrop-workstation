# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Install latest Whonix template, configure apparmor on installed templates,
# and ensure sys-whonix and anon-whonix use latest version.
##

include:
  - securedrop_salt.sd-upgrade-templates

{% set sd_supported_whonix_version = '17' %}

whonix-gateway-installed:
  qvm.template_installed:
    - name: whonix-gateway-{{ sd_supported_whonix_version }}
    - fromrepo: qubes-templates-community

whonix-workstation-installed:
  qvm.template_installed:
    - name: whonix-workstation-{{ sd_supported_whonix_version }}
    - fromrepo: qubes-templates-community

dom0-enabled-apparmor-on-whonix-gw-template:
  qvm.vm:
    - name: whonix-gateway-{{ sd_supported_whonix_version }}
    - prefs:
      - kernelopts: "apparmor=1 security=apparmor"
    - require:
      - sls: securedrop_salt.sd-upgrade-templates
      - qvm: whonix-gateway-installed
      - qvm: whonix-workstation-installed

dom0-enabled-apparmor-on-whonix-ws-template:
  qvm.vm:
    - name: whonix-workstation-{{ sd_supported_whonix_version }}
    - prefs:
      - kernelopts: "apparmor=1 security=apparmor"
    - require:
      - sls: securedrop_salt.sd-upgrade-templates
      - qvm: whonix-gateway-installed
      - qvm: whonix-workstation-installed

# The Qubes logic is too polite about enforcing template
# settings, using "present" rather than "prefs". Below
# we force the template updates.
sys-whonix-template-config:
  qvm.vm:
    - name: sys-whonix
    - prefs:
      - template: whonix-gateway-{{ sd_supported_whonix_version }}
    - require:
      - qvm: dom0-enabled-apparmor-on-whonix-gw-template

anon-whonix-template-config:
  qvm.vm:
    - name: anon-whonix
    - prefs:
      - template: whonix-workstation-{{ sd_supported_whonix_version }}
    - require:
      - qvm: dom0-enabled-apparmor-on-whonix-ws-template
