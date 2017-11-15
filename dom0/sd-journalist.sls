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

# Allow our dispvm and sd-svs to send us progress updates
# Create an empty file if it doesn't already exist
/etc/qubes-rpc/policy/sd-process.Feedback:
  file.managed:    
    - source: ~
    - user: root
    - group: root
    - mode: 644

# XXX this did not work, did not add lines to the empty file...
# seems like file.line could work here
sed -i '1i$tag:sd-decrypt-vm sd-journalist allow' /etc/qubes-rpc/policy/sd-process.Feedback:
  cmd.run:
  - unless: grep -qF '$tag:sd-decrypt-vm sd-journalist allow' /etc/qubes-rpc/policy/sd-process.Feedback

sed -i '1isd-svs sd-journalist allow' /etc/qubes-rpc/policy/sd-process.Feedback:
  cmd.run:
  - unless: grep -qF 'sd-svs sd-journalist allow' /etc/qubes-rpc/policy/sd-process.Feedback
