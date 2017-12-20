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
#  - sd-whonix

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

# Allow dispvms based on this vm to use sd-gpg
sed -i '1isd-journalist $dispvm:sd-dispvm allow' /etc/qubes-rpc/policy/qubes.OpenInVM:
  cmd.run:
  - unless: grep -qF 'sd-journalist $dispvm:sd-dispvm allow' /etc/qubes-rpc/policy/qubes.OpenInVM

/etc/qubes-rpc/policy/sd-process.Feedback:
  file.managed:    
    - source: salt://sd/sd-journalist/sd-process.Feedback-dom0
    - user: root
    - group: root
    - mode: 644
