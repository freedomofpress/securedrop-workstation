# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-journalist-vault
# ========
#
# Sets up networkless app qube for journalists' secrets.
#
#

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}

include:
  - securedrop_salt.sd-workstation-template


sd-journalist-vault:
  qvm.vm:
    - name: sd-journalist-vault
    - present:
      - label: black
      - template: sd-inbox-debian-{{ sdvars.debian_version }}
    - prefs:
      - template: sd-inbox-debian-{{ sdvars.debian_version }}
      - netvm: ""
      - autostart: false
      - default_dispvm: ""
      # NOTE: not denied due to some features requiring USB attachment
      # - devices_denied: '*******'
    - features:
      - enable:
        - service.paxctld
        - service.securedrop-setup-journalist-vault
      - set:
        - menu-items: "org.keepassxc.KeePassXC.desktop"
    - tags:
      - add:
        - sd-workstation
        - sd-journalist
    - require:
      - sls: securedrop_salt.sd-workstation-template
