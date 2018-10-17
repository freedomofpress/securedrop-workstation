# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

configure apt-test apt repo:
  pkgrepo.managed:
    - name: "deb [arch=amd64] https://apt-test-qubes.freedom.press stretch main"
    - file: /etc/apt/sources.list.d/fpf-apt-test.list
    - key_url: "salt://sd/sd-workstation/apt-test-pubkey.asc"

configure mimetype support for debian9:
  pkg.installed:
    - pkgs:
      - securedrop-workstation-config
      - securedrop-workstation-grsec
