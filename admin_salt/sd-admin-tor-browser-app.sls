# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# AppVM-private durable state. This state must target sd-admin itself: files
# created in its TemplateVM outside /home would not persist across AppVM boots.

manage-securedrop-tor-browser-state:
  file.directory:
    - name: /home/user/.local/share/securedrop-tor-browser
    - user: user
    - group: user
    - mode: "0700"
    - makedirs: true

manage-securedrop-tor-browser-onion-auth-directory:
  file.directory:
    - name: /home/user/.local/share/securedrop-tor-browser/onion-auth
    - user: user
    - group: user
    - mode: "0700"
    - clean: true
    - exclude:
      - app-journalist.auth_private
    - require:
      - file: manage-securedrop-tor-browser-state

install-securedrop-tor-browser-onion-auth:
  file.managed:
    - name: /home/user/.local/share/securedrop-tor-browser/onion-auth/app-journalist.auth_private
    - source: salt://admin_salt/app-journalist.auth_private
    - user: user
    - group: user
    - mode: "0600"
    - require:
      - file: manage-securedrop-tor-browser-onion-auth-directory
