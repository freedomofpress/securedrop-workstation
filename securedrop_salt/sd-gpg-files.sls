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

sd-gpg-create-keyring-directory:
  file.directory:
    - name: /home/user/.gnupg
    - user: user
    - group: user
    - mode: 700

sd-gpg-import-submission-key:
  file.managed:
    - name: /home/user/.gnupg/sd-journalist.sec
    - source: salt://securedrop_salt/sd-journalist.sec
    - user: user
    - group: user
    - mode: 600
    # Don't print private key to stdout
    - show_changes: False
    - require:
      - file: sd-gpg-create-keyring-directory
  cmd.run:
    - name: sudo -u user gpg --import /home/user/.gnupg/sd-journalist.sec
    - require:
      - file: sd-gpg-import-submission-key
    - onchanges:
      - file: sd-gpg-import-submission-key
