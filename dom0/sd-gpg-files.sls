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
        export QUBES_GPG_AUTOACCEPT=28800

sd-gpg-import-submission-key:
  file.managed:
    - name: /tmp/sd-journalist.sec
    - source: salt://sd/sd-journalist.sec
    - user: user
    - group: user
    - mode: 644
    # Don't print private key to stdout
    - show_changes: False
  cmd.run:
    - name: sudo -u user gpg --import /tmp/sd-journalist.sec
    - require:
      - file: sd-gpg-import-submission-key
