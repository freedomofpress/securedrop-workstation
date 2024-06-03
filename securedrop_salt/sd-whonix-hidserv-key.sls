# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

{% import_json "securedrop_salt/config.json" as d %}

sd-whonix-hidservv3-directory-path:
  file.blockreplace:
    - name: /usr/local/etc/torrc.d/50_user.conf
    - append_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: ClientOnionAuthDir /var/lib/tor/keys

{% set hostname_without_onion = d.hidserv.hostname.split('.')[0] %}
install-sd-whonix-tor-private-key:
  file.managed:
    - name: /var/lib/tor/keys/app-journalist.auth_private
    - source: salt://securedrop_salt/app-journalist.yaml
    - template: jinja
    - context:
        hostname: {{ hostname_without_onion }}
        key: {{ d.hidserv.key }}
    - mode: 0600
    - user: debian-tor
    - group: debian-tor
