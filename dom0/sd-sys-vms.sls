# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# Ensures that sys-* VMs (viz. sys-net, sys-firewall, sys-usb) use
# an up-to-date version of Fedora, in order to receive security updates.

include:
  # Import the upstream Qubes-maintained default-dispvm to ensure Fedora-based
  # DispVM is created
  - qvm.default-dispvm

{% set sd_supported_fedora_version = 'fedora-35' %}


# Install latest templates required for SDW VMs.
dom0-install-fedora-template:
{% if grains['osrelease'] == '4.1' %}
  cmd.run:
    - name: >
        qvm-template install fedora-35
{% else %}
  pkg.installed:
    - pkgs:
      - qubes-template-{{ sd_supported_fedora_version }}
{% endif %}

# Update the mgmt VM before updating the new Fedora VM. The order is required
# and listed in the release notes for F32 & F33.
set-fedora-template-as-default-mgmt-dvm:
  cmd.run:
    - name: >
        qvm-shutdown --wait default-mgmt-dvm &&
        qvm-prefs default-mgmt-dvm template {{ sd_supported_fedora_version }}
    - require:
{% if grains['osrelease'] == '4.1' %}
      - cmd: dom0-install-fedora-template
{% else %}
      - pkg: dom0-install-fedora-template
{% endif %}

# If the VM has just been installed via package manager, update it immediately
update-fedora-template-if-new:
  cmd.wait:
    - name: sudo qubesctl --skip-dom0 --targets {{ sd_supported_fedora_version }} state.sls update.qubes-vm
    - require:
{% if grains['osrelease'] == '4.1' %}
      - cmd: dom0-install-fedora-template
{% else %}
      - pkg: dom0-install-fedora-template
{% endif %}
      # Update the mgmt-dvm setting first, to avoid problems during first update
      - cmd: set-fedora-template-as-default-mgmt-dvm
    - watch:
{% if grains['osrelease'] == '4.1' %}
      - cmd: dom0-install-fedora-template
{% else %}
      - pkg: dom0-install-fedora-template
{% endif %}

# qvm.default-dispvm is not strictly required here, but we want it to be
# updated as soon as possible to ensure make clean completes successfully, as
# is sets the default_dispvm to the DispVM based on the wanted Fedora version.
set-fedora-default-template-version:
  cmd.run:
    - name: qubes-prefs default_template {{ sd_supported_fedora_version }}
    - require:
{% if grains['osrelease'] == '4.1' %}
      - cmd: dom0-install-fedora-template
{% else %}
      - pkg: dom0-install-fedora-template
{% endif %}
      - sls: qvm.default-dispvm

# sys-usb qubes are disposable in the default configuration - instead of forcing
# users to turn sys-usb into an AppVM, we're just cloning the DispVM template to
# make our changes to allow auto-attaching USB drives. 
{% if grains['osrelease'] == '4.1' and salt['pillar.get']('qvm:sys-usb:disposable', true) %}
clone-dispvm-for-sys-usb-customization:
  cmd.run:
    - name: >
        qvm-check sd-fedora-dvm || qvm-clone {{ sd_supported_fedora_version }}-dvm sd-fedora-dvm
    - require:
      - cmd: dom0-install-fedora-template
{% endif %}


# Now proceed with rebooting all the sys-* VMs, since the new template is up to date.

{% for sys_vm in ['sys-usb', 'sys-net', 'sys-firewall'] %}
{% if grains['osrelease'] == '4.1' and salt['pillar.get']('qvm:'+sys_vm+':disposable', false) %}
# As of Qubes 4.1, certain sys-* VMs will be DispVMs by default.
{% if sys_vm == 'sys-usb' %}
# If sys-usb is disposable, we want it to use the template we just cloned so we
# can customize it
{% set sd_supported_fedora_template = 'sd-fedora-dvm' %}
{% else %}
{% set sd_supported_fedora_template = sd_supported_fedora_version+'-dvm' %}
{% endif %}
{% else %}
{% set sd_supported_fedora_template = sd_supported_fedora_version %}
{% endif %}
{% if salt['cmd.shell']('qvm-prefs '+sys_vm+' template') != sd_supported_fedora_template %}
sd-{{ sys_vm }}-fedora-version-halt:
  qvm.kill:
    - name: {{ sys_vm }}
    - require:
{% if grains['osrelease'] == '4.1' %}
      - cmd: dom0-install-fedora-template
{% else %}
      - pkg: dom0-install-fedora-template
{% endif %}

sd-{{ sys_vm }}-fedora-version-halt-wait:
  cmd.run:
    - name: sleep 5
    - require:
{% if grains['osrelease'] == '4.1' %}
      - cmd: dom0-install-fedora-template
{% else %}
      - pkg: dom0-install-fedora-template
{% endif %}

sd-{{ sys_vm }}-fedora-version-update:
  qvm.vm:
    - name: {{ sys_vm }}
    - prefs:
      - template: {{ sd_supported_fedora_template }}
    - require:
      - cmd: sd-{{ sys_vm }}-fedora-version-halt-wait

sd-{{ sys_vm }}-fedora-version-start:
  qvm.start:
    - name: {{ sys_vm }}
    - require:
      - qvm: sd-{{ sys_vm }}-fedora-version-update
{% endif %}
{% endfor %}
