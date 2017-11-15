# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-dispvm
# ========
#
# Configures the 'sd-disp' template VM, which will be used as the base dispvm
# for the securedrop client. Later we should create multiple dispvms for
# different purposes, but this ports the 3.2 behavior fow now.
# This VM has no network configured.
##

{%- from "qvm/template.jinja" import load -%}

{% load_yaml as defaults -%}
name:         sd-dispvm
present:
  - label:    green
prefs:
  - netvm:    ""
{%- endload %}

{{ load(defaults) }}

# tell qubes this VM can be used as a disp VM template
qvm-prefs sd-dispvm template_for_dispvms True:
  cmd.run

# tag this vm, since we need to set policies using it as a source
# (eg, "dispvms created from this VM can use the Gpg facility provided
.# by sd-gpg"), but the "$dispvm:sd-dispvm" syntax can only be used as an
# RPC policy *target*, not source. Tagged VMs can be used as a source.
# This feels like a Qubes bug.
qvm-tags sd-dispvm add sd-decrypt-vm:
  cmd.run

# Allow dispvms based on this vm to use sd-gpg
sed -i '1i$tag:sd-decrypt-vm sd-gpg allow' /etc/qubes-rpc/policy/qubes.Gpg:
  cmd.run:
  - unless: grep -qF '$tag:sd-decrypt-vm sd-gpg allow' /etc/qubes-rpc/policy/qubes.Gpg

# Allow dispvms based on this vm to open files in sd-svs
sed -i '1i$tag:sd-decrypt-vm sd-svs allow' /etc/qubes-rpc/policy/qubes.OpenInVM:
  cmd.run:
  - unless: grep -qF '$tag:sd-decrypt-vm sd-svs allow' /etc/qubes-rpc/policy/qubes.OpenInVM
