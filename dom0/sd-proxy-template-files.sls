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

# TEMPORARY: installs local deb for debugging
install-securedrop-proxy-package:
 file.managed:
   - name: /opt/securedrop-proxy.deb
   - source: salt://sd/sd-workstation/securedrop-proxy_0.3.0+buster_all.deb
   - mode: 644
 cmd.run:
  - name: apt install -y /opt/securedrop-proxy.deb


{% import_json "sd/config.json" as d %}

install-securedrop-proxy-yaml-config:
  file.managed:
    - name: /etc/sd-proxy.yaml
    - source: salt://sd/sd-proxy/sd-proxy.yaml
    - template: jinja
    - context:
        hostname: {{ d.hidserv.hostname }}
    - mode: 0644
