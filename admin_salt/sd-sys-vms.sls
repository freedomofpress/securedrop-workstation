# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# Ensures that sys-* VMs (viz. sys-net, sys-firewall, sys-usb) use
# an up-to-date version of Fedora, in order to receive security updates.
#
# This only runs if the journalist workstation is not installed.
# It is a near-copy of securedrop_salt/sd-sys-vms.sls, except we don't
# enable the auto-attach logic in sys-usb or care that it is disposable.

{% if not salt['file.file_exists']('/usr/share/securedrop/products/journalist-workstation.json') %}

include:
  # Import the upstream Qubes-maintained default-dispvm to ensure Fedora-based
  # DispVM is created.
  # WARNING: this includes indirectly 'qvm.preload-disposables', which reverts
  # any temporary disabling of disposable preloading. To avoid this, the pillar
  # 'qvm:dom0:preload' needs to be overridden as 'false'.
  - qvm.default-dispvm

# 4.2 fedora template is fedora-NN-xfce, but let's keep the dvm names to
# follow simple - like sd-fedora-NN-dvm
{% set sd_supported_fedora_version_num = 43 %}
{% set sd_supported_fedora_version = 'fedora-' ~ sd_supported_fedora_version_num %}
{% set sd_fedora_base_template = sd_supported_fedora_version + '-xfce' %}

{% set gui_user = salt['cmd.shell']('groupmems -l -g qubes') %}

# Install latest templates required for SDW VMs.
dom0-install-fedora-template:
  qvm.template_installed:
    - name: {{ sd_fedora_base_template }}

# Update the mgmt VM before updating the new Fedora VM. The order is required
set-fedora-template-as-default-mgmt-dvm:
  cmd.run:
    - name: >
        qvm-shutdown --wait default-mgmt-dvm &&
        qvm-prefs default-mgmt-dvm template {{ sd_fedora_base_template }}
    - require:
      - qvm: dom0-install-fedora-template

# Newly template is up to date before proceeding with VM configuration:
#  1. VM configuration via salt uses management qubes. Any bugs in the official
#     template, especially salt-related could brick VM configuration completely
#     (e.g. https://github.com/freedomofpress/securedrop-workstation/pull/1638#issuecomment-4350992151)
#  2. This state is run via the GUI updater (as part of its routine dom0 highstate
#     run), it ensures that updates are applied to a new template even if the
#     running updater has a stale list
#     (see https://github.com/freedomofpress/securedrop-workstation/issues/758)
update-fedora-template-if-new:
  cmd.run:
    - name: qubes-vm-update --quiet --force-update --targets {{ sd_fedora_base_template }}
    - runas: {{ gui_user }}
    - require:
      # Update the mgmt-dvm setting first, to avoid problems during first update
      - cmd: set-fedora-template-as-default-mgmt-dvm
    - unless:
      # Run if never updated (likely a clean install or just downloaded template)
      - qvm-features {{ sd_fedora_base_template }} last-update

# qvm.default-dispvm is not strictly required here, but we want it to be
# updated as soon as possible to ensure make clean completes successfully, as
# is sets the default_dispvm to the DispVM based on the wanted Fedora version.
set-fedora-default-template-version:
  cmd.run:
    - name: qubes-prefs default_template {{ sd_fedora_base_template }}
    - require:
      - qvm: dom0-install-fedora-template
      - sls: qvm.default-dispvm

# On 4.1, several sys qubes are disposable by default - since we also want to
# upgrade the templates for those, we need to ensure that the respective dvms
# exist, as just installing a new template won't create a DispVM template
# automatically.
{% set required_dispvms = [ sd_supported_fedora_version + '-dvm' ] %}

{% for required_dispvm in required_dispvms %}
create-{{ required_dispvm }}:
  qvm.vm:
    - name: {{ required_dispvm }}
    - present:
      - label: red
      - template: {{ sd_fedora_base_template }}
    - prefs:
      - template: {{ sd_fedora_base_template }}
      - template_for_dispvms: True
    - require:
      - qvm: dom0-install-fedora-template
{% endfor %}

# Now proceed with rebooting all the sys-* VMs, since the new template is up to date.

{% for sys_vm in ['sys-usb', 'sys-net', 'sys-firewall'] %}
{% if salt['pillar.get']('qvm:' + sys_vm + ':disposable', false) %}
# As of Qubes 4.1, certain sys-* VMs will be DispVMs by default.
  {% set sd_supported_fedora_template = sd_supported_fedora_version + '-dvm' %}
{% else %}
  {% set sd_supported_fedora_template = sd_fedora_base_template %}
{% endif %}
{% if salt['cmd.shell']('qvm-prefs ' + sys_vm + ' template') != sd_supported_fedora_template %}
sd-{{ sys_vm }}-fedora-version-halt:
  qvm.shutdown:
    - name: {{ sys_vm }}
      flags:
        - wait
        - force
    - require:
      - qvm: dom0-install-fedora-template

sd-{{ sys_vm }}-fedora-version-update:
  qvm.vm:
    - name: {{ sys_vm }}
    - prefs:
      - template: {{ sd_supported_fedora_template }}
    - require:
      - qvm: sd-{{ sys_vm }}-fedora-version-halt
{% if sd_supported_fedora_template.endswith("-dvm") %}
      - qvm: create-{{ sd_supported_fedora_template }}
{% endif %}

sd-{{ sys_vm }}-fedora-version-start:
  qvm.start:
    - name: {{ sys_vm }}
    - require:
      - qvm: sd-{{ sys_vm }}-fedora-version-update
{% endif %}
{% endfor %}


# Finally, remove the old supported fedora DVMs we created. We won't uninstall
# the template, in case it's being used elsewhere, but the DVMs we created
# ourselves we can reasonably manage (remove).
{% set curr_fedora = sd_supported_fedora_version_num|string %}
{% set prev_fedora = (sd_supported_fedora_version_num - 1)|string %}
{% for curr_dispvm_template in required_dispvms %}
  {% set prev_dispvm_template = curr_dispvm_template | replace(curr_fedora, prev_fedora) %}
remove-{{ prev_dispvm_template }}:
  qvm.absent:
    - name: {{ prev_dispvm_template }}
    - require:
      - qvm: create-{{ curr_dispvm_template }}
{% endfor %}

{% endif %}
