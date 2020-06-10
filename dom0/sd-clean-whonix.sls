# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# removes securedrop-log rsyslog plugin in whonix-gw-15
##

remove-securedrop-log-package-from-whonix:
  pkg.purged:
    - pkgs:
      - securedrop-log
      - securedrop-keyring

sd-cleanup-whonix-gw-15:
  cmd.run:
    - names:
      - sudo rm -f /etc/rsyslog.d/sdlog.conf
      - sudo rm -f /etc/apt/sources.list.d/securedrop_workstation.list
      - sudo systemctl restart rsyslog
      - sudo apt-key del 4ED79CC3362D7D12837046024A3BE4A92211B03C
