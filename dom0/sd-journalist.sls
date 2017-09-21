# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.work
# ========
#
# Installs 'sd-journlist' AppVM, for hosting the securedrop workstation app
#
##

include:
  - sd-whonix

{%- from "qvm/template.jinja" import load -%}

{% load_yaml as defaults -%}
name:         sd-journalist
present:
  - template: sd-journalist-whonix-ws
  - label:    blue
prefs:
  - netvm:    sd-whonix
require:
  - qvm:      sd-whonix

{%- endload %}

{{ load(defaults) }}
