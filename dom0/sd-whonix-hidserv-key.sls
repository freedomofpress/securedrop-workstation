# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

{% import_json "sd/config.json" as d %}

# add hidden service auth key to torrc
{% if d.hidserv.hostname|length == 22 %}
sd-whonix-hidserv-key:
  file.append:
    - name: /usr/local/etc/torrc.d/50_user.conf
    - text: HidServAuth {{ d.hidserv.hostname }} {{ d.hidserv.key }}
{% else %}
sd-whonix-hidservv3-directory-path:
  file.append:
    - name: /usr/local/etc/torrc.d/50_user.conf
    - text: ClientOnionAuthDir /var/lib/tor/keys

{% set hostname_without_onion = d.hidserv.hostname.split('.')[0] %}
install-sd-whonix-tor-private-key:
  file.managed:
    - name: /var/lib/tor/keys/app-journalist.auth_private
    - source: salt://sd/sd-whonix/app-journalist.yaml
    - template: jinja
    - context:
        hostname: {{ hostname_without_onion }}
        key: {{ d.hidserv.key }}
    - mode: 0600
    - user: debian-tor
    - group: debian-tor
{% endif %}
