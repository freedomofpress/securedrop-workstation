# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-svs-disp
# ========
#
# Configures the 'sd-svs-disp' template VM, which will be used as the
# base dispvm for the SVS vm (will be used to open all submissions
# after processing).
# This VM has no network configured.
##

{%- from "qvm/template.jinja" import load -%}

{% load_yaml as defaults -%}
name:         sd-svs-disp
present:
  - template: fedora-28
  - label:    green
prefs:
  - netvm:    ""
{%- endload %}

{{ load(defaults) }}

# tell qubes this VM can be used as a disp VM template
qvm-prefs sd-svs-disp template_for_dispvms True:
  cmd.run

# Allow dispvms based on this vm to open files in sd-svs.
# See note in sd-decrypt.sls about why we tag here.
qvm-tags sd-svs-disp add sd-svs-disp-vm:
  cmd.run

/etc/qubes-rpc/policy/qubes.OpenInVM:
  file.line:
    - content: $tag:sd-svs-disp-vm sd-svs allow
    - mode: insert
    - location: start
