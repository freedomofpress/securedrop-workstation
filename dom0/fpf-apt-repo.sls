# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#

# Don't start with the Qubes-maintained Salt logic for upgrading VM packages:
#
#   dom0:/srv/formulas/base/update-formula/update/qubes-vm.sls
#
# We want to make sure that certain maintenance tasks like cleaning out
# old packages and updating apt lists are handled first, otherwise
# the subsequent tasks will fail. For reference
# include:
#  - update.qubes-vm
#  - sd-default-config

# Imports "sdvars" for environment config
{% from 'sd-default-config.sls' import sdvars with context %}

# Debian Buster was changed from 'stable' to 'oldstable' on 2021-08,
# so honor that change in the apt sources.
update-apt-cache-with-stable-change:
  cmd.run:
    - name: apt-get update --allow-releaseinfo-change

autoremove-old-packages:
  cmd.run:
    - name: apt-get autoremove -y
    - require:
      - cmd: update-apt-cache-with-stable-change

# That's right, we need to install a package in order to
# configure a repo to install another package
install-python-apt-for-repo-config:
  pkg.installed:
    - pkgs:
      - python3-apt
    - require:
      - cmd: update-apt-cache-with-stable-change
      - cmd: autoremove-old-packages

configure-fpf-apt-repo:
  pkgrepo.managed:
    # Can't reuse sdvars.distribution here because this queries grains from VMs
    # rather than dom0
    - name: "deb [arch=amd64] {{ sdvars.apt_repo_url }} {{ grains['oscodename'] }} {{ sdvars.component }}"
    - file: /etc/apt/sources.list.d/securedrop_workstation.list
    - key_url: "salt://sd/sd-workstation/{{ sdvars.signing_key_filename }}"
    - clean_file: True # squash file to ensure there are no duplicates
    - require:
      - pkg: install-python-apt-for-repo-config

upgrade-all-packages:
  pkg.uptodate:
    # Update apt lists again, since they were updated before FPF repo was added.
    - refresh: True
    - dist_upgrade: True
    - require:
      - pkgrepo: configure-fpf-apt-repo
      - cmd: update-apt-cache-with-stable-change

# This will install the production keyring package. This package will delete
# the prod key from the default keyring in /etc/apt/trusted.gpg but will
# preserve the apt-test key in this default keyring.
install-securedrop-keyring-package:
  pkg.installed:
    - pkgs:
      - securedrop-keyring
    - require:
      - pkgrepo: configure-fpf-apt-repo
