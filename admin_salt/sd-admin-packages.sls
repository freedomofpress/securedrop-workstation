# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Configures the FPF apt repository and installs securedrop-admin
# inside the sd-admin-trixie-template VM.
#
# Mirrors the approach in securedrop_salt/fpf-apt-repo.sls and
# securedrop_salt/sd-base-template-packages.sls, but uses duplicated
# .j2 templates and a self-contained config to keep the admin package
# independent of the workstation package.
##

{% from 'admin_salt/sd-admin-config.sls' import admin_vars with context %}

update-apt-cache:
  cmd.run:
    - name: apt-get update --allow-releaseinfo-change

autoremove-old-packages:
  cmd.run:
    - name: apt-get autoremove -y
    - require:
      - cmd: update-apt-cache

configure-fpf-apt-repo:
  file.managed:
    - name: "/etc/apt/sources.list.d/{{ admin_vars.apt_sources_filename }}"
    - source: "salt://admin_salt/{{ admin_vars.apt_sources_filename }}.j2"
    - template: jinja
    - context:
        codename: {{ grains['oscodename'] }}
        component: {{ admin_vars.component }}
    - require:
      - cmd: autoremove-old-packages

# TODO: there's no keyring for trixie yet
# install-securedrop-keyring:
#   pkg.installed:
#     - pkgs:
#       - securedrop-keyring
#     - require:
#       - file: configure-fpf-apt-repo

install-securedrop-admin:
  pkg.installed:
    - pkgs:
      - securedrop-admin
    - refresh: True
