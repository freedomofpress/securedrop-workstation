# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

/usr/bin/move-to-svs:
  file.managed:
    - source: salt://sd/sd-journalist/move-to-svs
    - user: root
    - group: root
    - mode: 755

/usr/bin/sd-process-download:
  file.managed:
    - source: salt://sd/sd-journalist/sd-process-download
    - user: root
    - group: root
    - mode: 755

/usr/bin/do-not-open-here:
  file.managed:
    - source: salt://sd/sd-journalist/do-not-open-here
    - user: root
    - group: root
    - mode: 755

/usr/bin/sd-process-feedback:
  file.managed:
    - source: salt://sd/sd-journalist/sd-process-feedback
    - user: root
    - group: root
    - mode: 755

/usr/bin/sd-process-display:
  file.managed:
    - source: salt://sd/sd-journalist/sd-process-display
    - user: root
    - group: root
    - mode: 644

/usr/bin/pipereader.py:
  file.managed:
    - source: salt://sd/sd-journalist/pipereader.py
    - user: root
    - group: root
    - mode: 755

/usr/share/applications/sd-process-download.desktop:
  file.managed:
    - source: salt://sd/sd-journalist/sd-process-download.desktop
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/usr/share/applications/do-not-open.desktop:
  file.managed:
    - source: salt://sd/sd-journalist/do-not-open.desktop
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/usr/share/sd/logo-small.png:
  file.managed:
    - source: salt://sd/sd-journalist/logo-small.png
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

/etc/qubes-rpc/sd-process.Feedback:
  file.managed:
    - source: salt://sd/sd-journalist/sd-process.Feedback
    - user: root
    - group: root
    - mode: 644
    - makedirs: True

sudo update-desktop-database /usr/share/applications:
  cmd.run

# Depends on FPF-controlled apt repo, already present
# in underlying "securedrop-workstation" base template.
install-securedrop-proxy-package:
  pkg.installed:
    - pkgs:
      - securedrop-proxy
  require:
    - sls: fpf-apt-test-repo

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
