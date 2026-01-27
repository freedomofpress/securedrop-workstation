# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Installs dom0 config scripts specific to tracking updates
# over time. These scripts should be ported to an RPM package.
##

# Ensure debian-12-minimal is present for use as base template
dom0-install-debian-minimal-template:
  qvm.template_installed:
    - name: debian-12-minimal

{% set gui_user = salt['cmd.shell']('groupmems -l -g qubes') %}
{% import_json "securedrop_salt/config.json" as d %}

dom0-login-autostart-directory:
  file.directory:
    - name: /home/{{ gui_user }}/.config/autostart
    - user: {{ gui_user }}
    - group: {{ gui_user }}
    - mode: 700
    - makedirs: True

dom0-login-autostart-desktop-file:
  file.managed:
    - name: /home/{{ gui_user }}/.config/autostart/press.freedom.SecureDropUpdater.desktop
    - source: "salt://securedrop_salt/dom0-xfce-desktop-file.j2"
    - template: jinja
    - context:
        desktop_name: SDWLogin
        desktop_comment: Updates SecureDrop Workstation DispVMs at login
        desktop_exec: /usr/bin/sdw-login{% if d.get('app', false) %} --launch-app{% endif %}
    - user: {{ gui_user }}
    - group: {{ gui_user }}
    - mode: 664
    - require:
      - file: dom0-login-autostart-directory

dom0-securedrop-launcher-desktop-shortcut:
  file.managed:
    - name: /home/{{ gui_user }}/Desktop/press.freedom.SecureDropUpdater.desktop
    - source: "salt://securedrop_salt/press.freedom.SecureDropUpdater.desktop.j2"
    - template: jinja
    - context:
        desktop_exec: sdw-updater{% if d.get('app', false) %} --launch-app{% endif %}
    - user: {{ gui_user }}
    - group: {{ gui_user }}
    - mode: 755

dom0-environment-directory:
  file.directory:
    - name: /var/lib/securedrop-workstation/
    - mode: 755
    - makedirs: true

dom0-remove-old-environment-flag:
  file.tidied:
    - name: /var/lib/securedrop-workstation/
    - require:
      - file: dom0-environment-directory

dom0-write-environment-flag:
  file.managed:
    - name: /var/lib/securedrop-workstation/{{ d.environment }}
    - mode: 644
    - replace: False
    - require:
      - file: dom0-remove-old-environment-flag
