# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
{% import_json "sd/config.json" as d %}

install-securedrop-proxy-yaml-config:
  file.managed:
    - name: /home/user/.securedrop_proxy/sd-proxy.yaml
    - source: salt://sd/sd-proxy/sd-proxy.yaml
    - makedirs: True
    - template: jinja
    - user: user
    - group: user
    - context:
        hostname: {{ d.hidserv.hostname }}
    - mode: 0644
