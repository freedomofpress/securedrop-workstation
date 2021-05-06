# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# Ensures that sys-* VMs (viz. sys-net, sys-firewall, sys-usb) use
# an up-to-date version of Fedora, in order to receive security updates.

include:
  # Import the upstream Qubes-maintained default-dispvm to ensure Fedora-based
  # DispVM is created
  - qvm.default-dispvm

{% set sd_supported_fedora_version = 'fedora-33' %}

# Install latest templates required for SDW VMs.
dom0-install-fedora-template:
  pkg.installed:
    - pkgs:
      - qubes-template-{{ sd_supported_fedora_version }}

# If the VM has just been installed via package manager, update it immediately
update-fedora-template-if-new:
  cmd.wait:
    - name: sudo qubesctl --skip-dom0 --targets {{ sd_supported_fedora_version }} state.sls update.qubes-vm
    - require:
      - pkg: dom0-install-fedora-template
    - watch:
      - pkg: dom0-install-fedora-template
# qvm.default-dispvm is not strictly required here, but we want it to be
# updated as soon as possible to ensure make clean completes successfully, as
# is sets the default_dispvm to the DispVM based on the wanted Fedora version.
set-fedora-default-template-version:
  cmd.run:
    - name: qubes-prefs default_template {{ sd_supported_fedora_version }}
    - require:
      - pkg: dom0-install-fedora-template
      - sls: qvm.default-dispvm

{% for sys_vm in ['sys-usb', 'sys-net', 'sys-firewall', 'default-mgmt-dvm'] %}
{% if salt['cmd.shell']('qvm-prefs '+sys_vm+' template') != sd_supported_fedora_version %}
sd-{{ sys_vm }}-fedora-version-halt:
  qvm.kill:
    - name: {{ sys_vm }}
    - require:
      - pkg: dom0-install-fedora-template

sd-{{ sys_vm }}-fedora-version-halt-wait:
  cmd.run:
    - name: sleep 5
    - require:
      - qvm: sd-{{ sys_vm }}-fedora-version-halt

sd-{{ sys_vm }}-fedora-version-update:
  qvm.vm:
    - name: {{ sys_vm }}
    - prefs:
      - template: {{ sd_supported_fedora_version }}
    - require:
      - cmd: sd-{{ sys_vm }}-fedora-version-halt-wait

sd-{{ sys_vm }}-fedora-version-start:
  qvm.start:
    - name: {{ sys_vm }}
    - require:
      - qvm: sd-{{ sys_vm }}-fedora-version-update
{% endif %}
{% endfor %}
