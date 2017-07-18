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
  - template: whonix-gw
  - label: purple
  - mem: 500
  - flags:
    - proxy
prefs:
  - netvm: sys-firewall
  - autostart: true
require:
  - pkg: template-whonix-gw
  - qvm: sys-firewall
{%- endload %}

{{ load(defaults) }}
