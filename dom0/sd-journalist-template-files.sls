# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

include:
  - fpf-apt-test-repo

sd-journalist-copy-do-not-open-here-script:
  file.managed:
    - name: /usr/bin/do-not-open-here
    - source: salt://sd/sd-journalist/do-not-open-here
    - user: root
    - group: root
    - mode: 755
    - require:
      - qvm: sd-journalist-template

sd-journalist-copy-do-not-open-here-desktop-file:
  file.managed:
    - name: /usr/share/applications/do-not-open.desktop
    - source: salt://sd/sd-journalist/do-not-open.desktop
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - require:
      - qvm: sd-journalist-template

sd-journalist-copy-sd-logo:
  file.managed:
    - name: /usr/share/sd/logo-small.png
    - source: salt://sd/sd-journalist/logo-small.png
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - require:
      - qvm: sd-journalist-template

sd-journalist-update-desktop-database:
  cmd.run:
    - name: sudo update-desktop-database /usr/share/applications
    - require:
      - qvm: sd-journalist-template
      - file: sd-journalist-copy-do-not-open-here-desktop-file

# Depends on FPF-controlled apt repo, already present
# in underlying "securedrop-workstation" base template.
install-securedrop-proxy-package:
  pkg.installed:
    - pkgs:
      - securedrop-proxy
    - require:
      - sls: fpf-apt-test-repo
      - qvm: sd-journalist-template

{% import_json "sd/config.json" as d %}

install-securedrop-proxy-yaml-config:
  file.append:
    - name: /etc/sd-proxy.yaml
    - text: |
        host: {{ d.hidserv.hostname }}
        scheme: http
        port: 80
        target_vm: sd-svs
        dev: False
    - require:
      - qvm: sd-journalist-template
