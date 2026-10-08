# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Configures the FPF apt repository and installs required packages
# inside the sd-admin-debian-13 template.
##

include:
  - admin_salt.fpf-apt-repo

# additional packages (eg. tor, keepassxc) are installed as securedrop-admin dependencies
# See https://github.com/freedomofpress/securedrop/blob/develop/admin/debian/control
install-securedrop-packages:
  pkg.installed:
    - pkgs:
      - securedrop-admin-qubes
      - securedrop-workstation-grsec
    - require:
      - pkg: upgrade-all-packages
      - pkg: install-securedrop-keyring-package
