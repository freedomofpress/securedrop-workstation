# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Installs 'sd-app' AppVM, to persistently store SD data
# This VM has no network configured.
##

# Imports "apt_config" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import apt_config with context %}

# Check environment
{% import_json "securedrop_salt/config.json" as d %}

include:
  - securedrop_salt.sd-workstation-template
  - securedrop_salt.sd-viewer

sd-app:
  qvm.vm:
    - name: sd-app
    - present:
      # Sets attributes if creating VM for the first time,
      # otherwise `prefs` must be used.
      # Label color is set during initial configuration but
      # not enforced on every Salt run, in case of user customization.
      - label: yellow
      - template: sd-small-{{ apt_config.distribution }}-template
    - prefs:
      - template: sd-small-{{ apt_config.distribution }}-template
      - netvm: ""
      - default_dispvm: "sd-viewer"
    - tags:
      - add:
        - sd-client
        - sd-workstation
    - features:
      - set:
        - vm-config.SD_MIME_HANDLING: sd-app
        - internal: ""
      - enable:
        - service.paxctld
        - service.securedrop-mime-handling
    - require:
      - qvm: sd-small-{{ apt_config.distribution }}-template
      - sls: securedrop_salt.sd-viewer

sd-app-config:
  qvm.features:
    - name: sd-app
    - set:
        - vm-config.QUBES_GPG_DOMAIN: sd-gpg
        - vm-config.SD_SUBMISSION_KEY_FPR: {{ d.submission_key_fpr }}

# The private volume size should be defined in the config.json
sd-app-private-volume-size:
  cmd.run:
    - name: >
        qvm-volume resize sd-app:private {{ d.vmsizes.sd_app }}GiB
    - require:
      - qvm: sd-app
