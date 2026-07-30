# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

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
