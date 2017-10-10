# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# qvm.work
# ========
#
# Installs 'sd-svs' AppVM, to persistently store SD data
# This VM has no network configured.
##

{%- from "qvm/template.jinja" import load -%}

{% load_yaml as defaults -%}
name:         sd-svs
present:
  - label:    yellow
prefs:
  - netvm:    ""
{%- endload %}

{{ load(defaults) }}
