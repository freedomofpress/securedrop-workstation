# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# Ensures that sys-* VMs (viz. sys-net, sys-firewall, sys-usb) use
# an up-to-date version of Fedora, in order to receive security updates.

include:
  # Import the upstream Qubes-maintained default-dispvm to ensure Fedora-based
  # DispVM is created
  - qvm.default-dispvm

# 4.2 fedora template is fedora-NN-xfce, but let's keep the dvm names to 
# follow simple - like sd-fedora-NN-dvm
{% set sd_supported_fedora_version = 'fedora-40' %}
{% set sd_fedora_base_template = sd_supported_fedora_version + '-xfce' %}

# Install latest templates required for SDW VMs.
dom0-install-fedora-template:
  cmd.run:
    - name: >
        qvm-template info --machine-readable {{ sd_fedora_base_template }} | grep -q "installed|{{ sd_fedora_base_template }}|" || qvm-template install {{ sd_fedora_base_template }}

# Update the mgmt VM before updating the new Fedora VM. The order is required
set-fedora-template-as-default-mgmt-dvm:
  cmd.run:
    - name: >
        qvm-shutdown --wait default-mgmt-dvm &&
        qvm-prefs default-mgmt-dvm template {{ sd_fedora_base_template }}
    - require:
      - cmd: dom0-install-fedora-template

# If the VM has just been installed via package manager, update it immediately
update-fedora-template-if-new:
  cmd.wait:
    - name: qubes-vm-update --quiet --force-update --targets {{ sd_fedora_base_template }}
    - require:
      - cmd: dom0-install-fedora-template
      # Update the mgmt-dvm setting first, to avoid problems during first update
      - cmd: set-fedora-template-as-default-mgmt-dvm
    - watch:
      - cmd: dom0-install-fedora-template

# qvm.default-dispvm is not strictly required here, but we want it to be
# updated as soon as possible to ensure make clean completes successfully, as
# is sets the default_dispvm to the DispVM based on the wanted Fedora version.
set-fedora-default-template-version:
  cmd.run:
    - name: qubes-prefs default_template {{ sd_fedora_base_template }}
    - require:
      - cmd: dom0-install-fedora-template
      - sls: qvm.default-dispvm

# On 4.1, several sys qubes are disposable by default - since we also want to
# upgrade the templates for those, we need to ensure that the respective dvms
# exist, as just installing a new template won't create a DispVM template
# automatically.
# sys-usb is also disposable by default but a special case as we want to
# customize the underlying DispVM template for usability purposes: we want to
# consistently auto-attach USB devices to our sd-devices qube
#
{% set required_dispvms = [ sd_supported_fedora_version + '-dvm' ] %}
{% if salt['pillar.get']('qvm:sys-usb:disposable', true) %}
  {% set _ = required_dispvms.append("sd-" + sd_supported_fedora_version + "-dvm") %}
{% endif %}

{% for required_dispvm in required_dispvms %}
create-{{ required_dispvm }}:
  qvm.vm:
    - name: {{ required_dispvm }}
    - present:
      - template: {{ sd_fedora_base_template }}
      - label: red
    - prefs:
      - template: {{ sd_fedora_base_template }}
      - template_for_dispvms: True
{% if required_dispvm == 'sd-' + sd_supported_fedora_version + '-dvm' %}
      - netvm: ""
{% endif %}
    - require:
      - cmd: dom0-install-fedora-template
{% endfor %}

# Now proceed with rebooting all the sys-* VMs, since the new template is up to date.

{% for sys_vm in ['sys-usb', 'sys-net', 'sys-firewall'] %}
{% if salt['pillar.get']('qvm:' + sys_vm + ':disposable', false) %}
# As of Qubes 4.1, certain sys-* VMs will be DispVMs by default.
  {% if sys_vm == 'sys-usb' %}
    # If sys-usb is disposable, we want it to use the template we just created so we
    # can customize it later in the process
    {% set sd_supported_fedora_template = 'sd-' + sd_supported_fedora_version + '-dvm' %}
  {% else %}
    {% set sd_supported_fedora_template = sd_supported_fedora_version + '-dvm' %}
  {% endif %}
{% else %}
  {% set sd_supported_fedora_template = sd_fedora_base_template %}
{% endif %}
{% if salt['cmd.shell']('qvm-prefs ' + sys_vm + ' template') != sd_supported_fedora_template %}
sd-{{ sys_vm }}-fedora-version-halt:
  qvm.kill:
    - name: {{ sys_vm }}
    - require:
      - cmd: dom0-install-fedora-template

sd-{{ sys_vm }}-fedora-version-halt-wait:
  cmd.run:
    - name: sleep 5
    - require:
      - cmd: dom0-install-fedora-template

sd-{{ sys_vm }}-fedora-version-update:
  qvm.vm:
    - name: {{ sys_vm }}
    - prefs:
      - template: {{ sd_supported_fedora_template }}
    - require:
      - cmd: sd-{{ sys_vm }}-fedora-version-halt-wait
{% if sd_supported_fedora_template.endswith("-dvm") %}
      - qvm: create-{{ sd_supported_fedora_template }}
{% endif %}

# Finally, remove the old supported fedora DVM we created. We won't uninstall
# the template, in case it's being used elsewhere, but the `sd-` VMs we can
# reasonably manage (remove) ourselves.
{% if sys_vm == "sys-usb" %}
remove-sd-fedora-39-dvm:
  qvm.absent:
    - name: sd-fedora-39-dvm
    - require:
      - qvm: sd-sys-usb-fedora-version-update
{% endif %}

sd-{{ sys_vm }}-fedora-version-start:
  qvm.start:
    - name: {{ sys_vm }}
    - require:
      - qvm: sd-{{ sys_vm }}-fedora-version-update
{% endif %}
{% endfor %}

