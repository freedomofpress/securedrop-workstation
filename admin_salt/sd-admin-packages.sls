# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Configures the FPF apt repository and installs required packages
# inside the sd-admin-debian-13 VM.
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

# Install qubes VM kernel support here, activate PVH in the sd-admin AppVM later
# TODO: add an fpf metapackage to manage these dependencies
install-qubes-packages:
  pkg.installed:
    - pkgs:
      - qubes-vm-recommended
      - linux-image-amd64
      - grub2
      - qubes-kernel-vm-support
      - xfce4-terminal

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

update-apt-cache-with-fpf:
  cmd.run:
    - name: apt-get update --allow-releaseinfo-change
    - require:
      - file: configure-fpf-apt-repo

# additional packages (eg. tor, keepassxc) are installed as securedrop-admin dependencies
# See https://github.com/freedomofpress/securedrop/blob/develop/admin/debian/control
install-securedrop-packages:
  pkg.installed:
    - pkgs:
      - securedrop-keyring
      - securedrop-admin
      - securedrop-workstation-grsec
    - require:
      - cmd: update-apt-cache-with-fpf
