# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-viewer
# ========
#
# Configures the 'sd-viewer' template VM, which will be used as the
# base dispvm for the SVS vm (will be used to open all submissions
# after processing).
# This VM has no network configured.
##

# Imports "apt_config" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import apt_config with context %}

include:
  - securedrop_salt.sd-workstation-template

sd-viewer:
  qvm.vm:
    - name: sd-viewer
    - present:
      # Sets attributes if creating VM for the first time,
      # otherwise `prefs` must be used.
      # Label color is set during initial configuration but
      # not enforced on every Salt run, in case of user customization.
      - label: green
      - template: sd-large-{{ apt_config.distribution }}-template
    - prefs:
      - template: sd-large-{{ apt_config.distribution }}-template
      - netvm: ""
      - template_for_dispvms: True
      - default_dispvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-viewer-vm
        - sd-{{ apt_config.distribution }}
    - features:
      - set:
        - vm-config.SD_MIME_HANDLING: sd-viewer
        {% if apt_config['env'] == "prod" %}
        - internal: 1
        {% else %}
        - internal: ""
        {% endif %}
      - enable:
        - service.paxctld
        - service.securedrop-mime-handling
    - require:
      - qvm: sd-large-{{ apt_config.distribution }}-template

# Set sd-viewer as the global default_dispvm
# While all of our VMs have explit default_dispvm set, this is a better default
# than the stock fedora-XX-dvm in case someone creates their own VMs.
sd-viewer-default-dispvm:
  cmd.run:
    - name: qubes-prefs default_dispvm sd-viewer
    - require:
      - qvm: sd-viewer
