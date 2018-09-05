# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-decrypt
# ========
#
# Configures the 'sd-decrypt' template VMs
# This should be a disposable VM, but due to a Qubes bug we're using a
# non-disposable VM for the time being.
##

{%- from "qvm/template.jinja" import load -%}

{% load_yaml as defaults -%}
name:         sd-decrypt
present:
  - template: fedora-28
  - label:    green
prefs:
  - netvm:    ""
{%- endload %}

{{ load(defaults) }}

# tell qubes this VM can be used as a disp VM template
qvm-prefs sd-decrypt template_for_dispvms True:
  cmd.run

# tag this vm, since we need to set policies using it as a source
# (eg, "dispvms created from this VM can use the Gpg facility provided
# by sd-gpg"), but the "$dispvm:sd-decrypt" syntax can only be used as an
# RPC policy *target*, not source. Tagged VMs can be used as a source.
# This feels like a Qubes bug.
qvm-tags sd-decrypt add sd-decrypt-vm:
  cmd.run

# Allow dispvms based on this vm to use sd-gpg
/etc/qubes-rpc/policy/qubes.Gpg:
  file.line:
    - content: $tag:sd-decrypt-vm sd-gpg allow
    - mode: insert
    - location: start

# Allow sd-decrypt to open files in sd-svs
/etc/qubes-rpc/policy/qubes.OpenInVM:
  file.line:
    - content: sd-decrypt sd-svs allow
    - mode: insert
    - location: start
