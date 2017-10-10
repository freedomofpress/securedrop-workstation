# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-gpg
# ========
#
# Installs 'sd-gpg' AppVM, to implement split GPG for SecureDrop
# This VM has no network configured.
##

{%- from "qvm/template.jinja" import load -%}

{% load_yaml as defaults -%}
name:         sd-gpg
present:
  - label:    purple
prefs:
  - netvm:    ""
{%- endload %}

{{ load(defaults) }}
