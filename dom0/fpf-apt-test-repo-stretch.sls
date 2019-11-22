# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
include:
  - update.qubes-vm

# That's right, we need to install a package in order to
# configure a repo to install another package
install-python-apt-for-stretch-repo-config:
  pkg.installed:
    - pkgs:
      - python-apt
    - require:
      # Require that the Qubes update state has run first
      - sls: update.qubes-vm

configure-apt-test-apt-repo-stretch:
  pkgrepo.managed:
    - name: "deb [arch=amd64] https://apt-test-qubes.freedom.press stretch main"
    - file: /etc/apt/sources.list.d/securedrop_workstation.list
    - key_url: "salt://sd/sd-workstation/apt-test-pubkey.asc"
    - clean_file: True # squash file to ensure there are no duplicates
    - require:
      - pkg: install-python-apt-for-stretch-repo-config
