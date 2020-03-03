# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# sd-app-files
# ========
#
# Moves files into place on sd-app-template
#
##
include:
  - fpf-apt-test-repo

# FPF repo is setup in "securedrop-workstation" template
install-securedrop-client-and-securedrop-log-package:
  pkg.installed:
    - pkgs:
      - securedrop-client
      - securedrop-log
    - require:
      - sls: fpf-apt-test-repo


sd-rsyslog-for-sd-app:
  file.managed:
    - name: /etc/sd-rsyslog.conf
    - source: "salt://sd-rsyslog.conf.j2"
    - template: jinja
    - context:
        vmname: sd-app-buster-template