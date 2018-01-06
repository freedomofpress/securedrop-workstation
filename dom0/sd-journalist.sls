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
  - qvm.template-whonix-ws
  - sd-whonix

{%- from "qvm/template.jinja" import load -%}

{% load_yaml as defaults -%}
name:         sd-journalist
present:
  - template: whonix-ws
  - label:    blue
prefs:
  - netvm:    sd-whonix
require:
  - pkg:      template-whonix-ws
  - qvm:      sd-whonix
{%- endload %}

{{ load(defaults) }}

# Allow sd-journslist to open files in sd-decrypt
sed -i '1isd-journalist sd-decrypt allow' /etc/qubes-rpc/policy/qubes.OpenInVM:
  cmd.run:
  - unless: grep -qF '1isd-journalist $dispvm:sd-decrypt allow' /etc/qubes-rpc/policy/qubes.OpenInVM

# Allow sd-journalist to open files in sd-decrypt-bsed dispVM's
# When our Qubes bug is fixed, this will be used.
sed -i '1isd-journalist $dispvm:sd-decrypt allow' /etc/qubes-rpc/policy/qubes.OpenInVM:
  cmd.run:
  - unless: grep -qF '1isd-journalist $dispvm:sd-decrypt allow' /etc/qubes-rpc/policy/qubes.OpenInVM

