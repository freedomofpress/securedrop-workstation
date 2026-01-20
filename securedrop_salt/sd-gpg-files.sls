# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-gpg-files
# ========
#
# Does hots config for sd-gpg split gpg AppVM
#
##

sd-gpg-increase-keyring-access-timeout:
  file.blockreplace:
    - name: /home/user/.profile
    - append_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        # hides GPG prompt (max epoch)
        export QUBES_GPG_AUTOACCEPT=2147483647
