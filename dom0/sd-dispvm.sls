# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-dispvm
# ========
#
# Installs 'sd-disp' AppVM, which will be used as the base dispvm for
# the securedrop client. Later we should create multiple dispvms for
# different purposes, but this ports the 3.2 behavior fow now.
# This VM has no network configured.
##

{%- from "qvm/template.jinja" import load -%}

{% load_yaml as defaults -%}
name:         sd-dispvm
present:
  - label:    red
prefs:
  - netvm:    ""
{%- endload %}

{{ load(defaults) }}

# tell qubes this VM can be used as a disp VM template
qvm-prefs sd-dispvm template_for_dispvms True:
  cmd.run
