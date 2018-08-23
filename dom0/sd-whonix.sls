# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.sd-whonix
# ==============
#
# Installs 'sd-whonix' ProxyVM for securedrop journalist workstation.
#
##

include:
  - qvm.template-whonix-gw
  - qvm.sys-firewall

{%- from "qvm/template.jinja" import load -%}

{% load_yaml as defaults -%}
name: sd-whonix
present:
  - template: whonix-gw-14
  - label: purple
  - mem: 500
prefs:
  - provides-network: true
  - netvm: sys-firewall
  - autostart: true
require:
  - pkg: qubes-template-whonix-gw-14
  - qvm: sys-firewall
{%- endload %}

{{ load(defaults) }}
