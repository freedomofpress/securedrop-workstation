# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# Handle misconfigured jessie-backports repo in default debian-9 TemplateVM.
# The Jessie repos aren't maintained anymore, and their inclusion causes
# even apt update to fail.
remove-jessie-backports-repo:
  file.line:
    - name: /etc/apt/sources.list
    # Unclear why "Delete" *must* be capitalized, but that's the case!
    - mode: delete
    - match: jessie-backports
    # quiet param seems to be ignored, so using "onlyif" to test existence
    - quiet: True
    - onlyif:
      - test -f /etc/apt/sources.list

# That's right, we need to install a package in order to
# configure a repo to install another package
install-python-apt-for-repo-config:
  pkg.installed:
    - pkgs:
      - python-apt
    - require:
      - file: remove-jessie-backports-repo

configure apt-test apt repo:
  pkgrepo.managed:
    - name: "deb [arch=amd64] https://apt-test-qubes.freedom.press stretch main"
    - file: /etc/apt/sources.list.d/fpf-apt-test.list
    - key_url: "salt://sd/sd-workstation/apt-test-pubkey.asc"
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
