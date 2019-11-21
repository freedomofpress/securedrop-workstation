# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# That's right, we need to install a package in order to
# configure a repo to install another package
install-python-apt-for-repo-config:
  pkg.installed:
    - pkgs:
      - python-apt

configure apt-test apt repo:
  pkgrepo.managed:
    - name: "deb [arch=amd64] https://apt-test-qubes.freedom.press buster main"
    - file: /etc/apt/sources.list.d/securedrop_workstation.list
    - key_url: "salt://sd/sd-workstation/apt-test-pubkey.asc"
    - clean_file: True # squash file to ensure there are no duplicates
    - require:
      - pkg: install-python-apt-for-repo-config

# Ensure all apt updates are applied, since the VMs
# will be cloned, duplicating package version drift.
update-all-apt-packages:
  pkg.uptodate:
    - cache_valid_time: "3600"
    - dist_upgrade: True
    - require:
      - pkg: install-python-apt-for-repo-config
