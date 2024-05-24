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
#  - securedrop_salt.sd-default-config

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}

# Using apt-get requires manual approval when releaseinfo changes,
# just get it over with in the beginning
update-apt-cache-with-stable-change:
  cmd.run:
    - name: apt-get update --allow-releaseinfo-change

autoremove-old-packages:
  cmd.run:
    - name: apt-get autoremove -y
    - require:
      - cmd: update-apt-cache-with-stable-change

# If we're on a prod environment, ensure there isn't a test .sources
# file. (Should never happen in real usage, but may in testing)
{% import_json "securedrop_salt/config.json" as d %}
{% if d.environment == "prod" %}
clean-old-test-sources:
  file.absent:
    - name: "/etc/apt/sources.list.d/apt-test_freedom_press.sources"
{% endif %}

# Install the relevant .sources file based on our environment.
configure-fpf-apt-repo:
  file.managed:
    - name: "/etc/apt/sources.list.d/{{ sdvars.apt_sources_filename }}"
    - source: "salt://securedrop_salt/{{ sdvars.apt_sources_filename }}.j2"
    - template: jinja
    - context:
        codename: {{ grains['oscodename'] }}
        component: {{ sdvars.component }}
    - require:
      - cmd: autoremove-old-packages
      {% if d.environment == "prod" %}
      - file: clean-old-test-sources
      {% endif %}

upgrade-all-packages:
  pkg.uptodate:
    # Update apt lists again, since they were updated before FPF repo was added.
    - refresh: True
    - dist_upgrade: True
    - require:
      - file: configure-fpf-apt-repo
      - cmd: update-apt-cache-with-stable-change

# Install production keyring package, which will overwrite prod .sources file
install-securedrop-keyring-package:
  pkg.installed:
    - pkgs:
      - securedrop-keyring
    - require:
      - file: configure-fpf-apt-repo
