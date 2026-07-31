# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

{% import_json "securedrop_salt/config.json" as d %}

install-securedrop-tor-browser-core:
  file.recurse:
    - name: /usr/lib/python3/dist-packages/securedrop_tor_browser
    - source: salt://admin_salt/securedrop_tor_browser
    - clean: true
    - file_mode: "0644"
    - dir_mode: "0755"
    - require:
      - pkg: install-securedrop-admin

install-securedrop-tor-browser-command:
  file.managed:
    - name: /usr/bin/securedrop-tor-browser
    - source: salt://admin_salt/securedrop-tor-browser
    - mode: "0755"
    - require:
      - file: install-securedrop-tor-browser-core

install-securedrop-tor-browser-desktop-entry:
  file.managed:
    - name: /usr/share/applications/press.freedom.SecureDropTorBrowser.desktop
    - source: salt://admin_salt/press.freedom.SecureDropTorBrowser.desktop
    - mode: "0644"
    - require:
      - file: install-securedrop-tor-browser-command

install-securedrop-tor-browser-icon:
  file.managed:
    - name: /usr/share/icons/hicolor/scalable/apps/securedrop-tor-browser.svg
    - source: salt://admin_salt/securedrop-tor-browser.svg
    - mode: "0644"
    - require:
      - file: install-securedrop-tor-browser-desktop-entry

install-securedrop-tor-browser-managed-config:
  file.managed:
    - name: /etc/securedrop/tor-browser.json
    - source: salt://admin_salt/tor-browser.json
    - mode: "0644"
    - makedirs: true

install-securedrop-tor-browser-policy:
  file.managed:
    - name: /etc/firefox/policies/policies.json
    - source: salt://admin_salt/tor-browser-policies.json.j2
    - template: jinja
    - context:
        onion_hostname: {{ d.hidserv.hostname }}
    - user: root
    - group: root
    - mode: "0644"
    - makedirs: true

install-securedrop-tor-browser-torrc:
  file.managed:
    - name: /etc/securedrop/tor-browser/torrc
    - source: salt://admin_salt/tor-browser-torrc
    - mode: "0644"
    - makedirs: true

install-securedrop-tor-browser-signing-key:
  file.managed:
    - name: /usr/share/securedrop-tor-browser/tor-browser-signing-key.asc
    - source: salt://admin_salt/tor-browser-signing-key.asc
    - mode: "0644"
    - makedirs: true

install-securedrop-tor-browser-minimum-version:
  file.managed:
    - name: /usr/share/securedrop-tor-browser/tor-browser-minimum-version
    - source: salt://admin_salt/tor-browser-minimum-version
    - mode: "0644"
    - makedirs: true

install-securedrop-tor-browser-firefox-apparmor:
  file.managed:
    - name: /etc/apparmor.d/securedrop-tor-browser-firefox
    - source: salt://admin_salt/tor-browser-firefox.apparmor
    - mode: "0644"

install-securedrop-tor-browser-tor-apparmor:
  file.managed:
    - name: /etc/apparmor.d/securedrop-tor-browser-tor
    - source: salt://admin_salt/tor-browser-tor.apparmor
    - mode: "0644"

enforce-securedrop-tor-browser-apparmor:
  cmd.run:
    - name: apparmor_parser --replace /etc/apparmor.d/securedrop-tor-browser-firefox /etc/apparmor.d/securedrop-tor-browser-tor
    - onchanges:
      - file: install-securedrop-tor-browser-firefox-apparmor
      - file: install-securedrop-tor-browser-tor-apparmor
