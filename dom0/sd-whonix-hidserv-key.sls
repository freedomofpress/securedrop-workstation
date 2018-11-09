# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :


include:
  - sd-whonix

{% import_json "sd/config.json" as d %}

# add hidden service auth key to torrc

sd-whonix-hidserv-key:
  file.append:
    - name: /usr/local/etc/torrc.d/50_user.conf
    - text: HidServAuth {{ d.hidserv.hostname }} {{ d.hidserv.key }}
    - require:
      - sls: sd-whonix
      - qvm: sd-whonix
