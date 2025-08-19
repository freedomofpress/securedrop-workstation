# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# Imports "apt_config" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import apt_config with context %}

include:
  - securedrop_salt.sd-dom0-files

# Clones a base templateVM from debian-12-minimal
sd-base-template:
  qvm.vm:
    - name: sd-base-{{ apt_config.distribution }}-template
    - clone:
      - source: debian-12-minimal
      - label: red
    - prefs:
      - default_dispvm: ""
    - tags:
      - add:
        - sd-workstation
        - sd-{{ apt_config.distribution }}
    - features:
      - enable:
        - service.paxctld
    - require:
      - qvm: dom0-install-debian-minimal-template

# Debian VMs need access to the signing key for initial provisioning; store it in
# salt cache, since they only have access to the cache and `/srv/salt`, not all of dom0.
# Using cp.push or cp.cache_file don't work due to the minion-minion setup and not wanting
# to make changes to the system Salt configuration.
# For public files only! Salt cache is readable by all minions.
cache-signing-key:
  cmd.run:
    - name: "cp {{ apt_config['keyfile'] }} /var/cache/salt/minion/files/base/securedrop_salt/signing-key-{{ apt_config['env'] }}"
