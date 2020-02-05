# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#

# Import the Qubes-maintained Salt logic for upgrading VM packages.
# Intelligently handles both Debian & Fedora VMs. For reference, see:
#
#   dom0:/srv/formulas/base/update-formula/update/qubes-vm.sls
#
include:
  - update.qubes-vm
#  - sd-default-config

{% from 'sd-default-config.sls' import sdvars with context %}

# That's right, we need to install a package in order to
# configure a repo to install another package
install-python-apt-for-repo-config:
  pkg.installed:
    - pkgs:
      - python-apt
    - require:
      # Require that the Qubes update state has run first. Doing so
      # will ensure that apt is sufficiently patched prior to installing.
      - sls: update.qubes-vm

configure-apt-test-apt-repo:
  pkgrepo.managed:
    - name: "deb [arch=amd64] {{ sdvars.apt_repo_url }} {{ grains['oscodename'] }} main"
    - file: /etc/apt/sources.list.d/securedrop_workstation.list
    - key_url: "salt://sd/sd-workstation/{{ sdvars.signing_key_filename }}"
    - clean_file: True # squash file to ensure there are no duplicates
    - require:
      - pkg: install-python-apt-for-repo-config
