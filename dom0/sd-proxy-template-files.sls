# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
include:
  - fpf-apt-test-repo
  - sd-logging-setup

sd-proxy-do-not-open-here-script:
  file.managed:
    - name: /usr/bin/do-not-open-here
    - source: salt://sd/sd-proxy/do-not-open-here
    - user: root
    - group: root
    - mode: 755

sd-proxy-do-not-open-here-desktop-file:
  file.managed:
    - name: /usr/share/applications/do-not-open.desktop
    - source: salt://sd/sd-proxy/do-not-open.desktop
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

sd-proxy-configure-mimetypes:
  file.managed:
    - name: /usr/share/applications/mimeapps.list
    - source: salt://sd/sd-proxy/mimeapps.list
    - user: user
    - group: user
    - mode: 644
    - makedirs: True
  cmd.run:
    - name: sudo update-desktop-database /usr/share/applications
    - require:
      - file: sd-proxy-configure-mimetypes
      - file: sd-proxy-do-not-open-here-desktop-file
      - file: sd-proxy-do-not-open-here-script
    - onchanges:
      - file: sd-proxy-do-not-open-here-script
      - file: sd-proxy-do-not-open-here-desktop-file
      - file: sd-proxy-configure-mimetypes

# Depends on FPF-controlled apt repo, already present
# in underlying "securedrop-workstation" base template.
install-securedrop-proxy-package:
  pkg.installed:
    - pkgs:
      - securedrop-proxy
    - require:
      - sls: fpf-apt-test-repo


{% import_json "sd/config.json" as d %}

install-securedrop-proxy-yaml-config:
  file.managed:
    - name: /etc/sd-proxy.yaml
    - source: salt://sd/sd-proxy/sd-proxy.yaml
    - template: jinja
    - context:
        hostname: {{ d.hidserv.hostname }}
    - mode: 0644
