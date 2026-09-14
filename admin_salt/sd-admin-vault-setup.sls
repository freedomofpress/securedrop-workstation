# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-admin-vault-setup
# ========
#
# copies over keepassxc template
#

# TODO: check the templateVM's actual username and use it here
# Copy the template keepassxc file to the (persistent) home dir
copy-keepassxc-template:
  file.managed:
    - name: "/home/user/Documents/securedrop-keepassx-example.kdbx"
    - source: "salt://admin_salt/files/securedrop-keepassx.kdbx"
    - user: user
    - group: user
    - mode: 755
    - makedirs: True
