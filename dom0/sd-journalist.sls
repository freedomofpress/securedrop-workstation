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
  - template: whonix-ws-14
  - label:    blue
prefs:
  - netvm:    sd-whonix
require:
  - pkg:      qubes-template-whonix-ws-14
  - qvm:      sd-whonix
{%- endload %}

{{ load(defaults) }}

/etc/qubes-rpc/policy/sd-process.Feedback:
  file.managed:
    - source: salt://sd/sd-journalist/sd-process.Feedback-dom0
    - user: root
    - group: root
    - mode: 644

# Temporary workaround to bootstrap Salt support on target.
qvm-run -a whonix-ws-14 "sudo apt-get install -qq python-futures":
  cmd.run

# Allow sd-journslist to open files in sd-decrypt
# When our Qubes bug is fixed, this will *not* be used
sed -i '1isd-journalist sd-decrypt allow' /etc/qubes-rpc/policy/qubes.OpenInVM:
  cmd.run:
    - unless: grep -qF 'sd-journalist sd-decrypt allow' /etc/qubes-rpc/policy/qubes.OpenInVM

# Allow sd-journalist to open files in sd-decrypt-bsed dispVM's
# When our Qubes bug is fixed, this will be used.
sed -i '1isd-journalist $dispvm:sd-decrypt allow' /etc/qubes-rpc/policy/qubes.OpenInVM:
  cmd.run:
  - unless: grep -qF 'sd-journalist $dispvm:sd-decrypt allow' /etc/qubes-rpc/policy/qubes.OpenInVM
