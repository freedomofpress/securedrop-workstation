# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#


# We need to run this early in the process because qubes will not allow us
# to swap templates for AppVMs that are used as Templates. As a result, we
# should do this early in the process, the rest of the run will ensure the
# configuration is properly applied

{% set sd_supported_debian_version = 'buster' %}

# if sd-svs-disp exists and it's not debian buster based, we should temporarily
# set the default dvm to another VM and delete it. It will be rebuild later
# in the run on a buster-based template
{% if 'sd-svs-disp' in salt['cmd.shell']('qvm-ls') %}
{% if sd_supported_debian_version not in salt['cmd.shell']('qvm-prefs sd-svs-disp template') %}
set-temporary-default-dvm:
  cmd.run:
    - name: qubes-prefs default_dispvm fedora-30-dvm

delete-sd-svs-disp-dvm:
  cmd.run:
    - name: qvm-remove -f sd-svs-disp
  require:
    - cmd: set-temporary-default-dvm

{% endif %}
{% endif %}

# If sd-export-usb-dvm exists and is not debian buster based, we should delete
# it.
{% if 'sd-export-usb-dvm' in salt['cmd.shell']('qvm-ls') %}
{% if sd_supported_debian_version not in salt['cmd.shell']('qvm-prefs sd-export-usb-dvm template') %}

delete-sd-export-usb-dvm:
  cmd.run:
    - name: qvm-remove -f sd-export-usb-dvm

{% endif %}
{% endif %}
