# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Installs dom0 config scripts specific to tracking updates
# over time. These scripts should be ported to an RPM package.
##

include:
  # Import the upstream Qubes-maintained anon-whonix settings.
  # The anon-whoni config pulls in sys-whonix and sys-firewall,
  # as well as ensures the latest versions of Whonix are installed.
  - qvm.anon-whonix

# Imports "sdvars" for environment config
{% from 'sd-default-config.sls' import sdvars with context %}

dom0-rpm-test-key:
  file.managed:
    # We write the pubkey to the repos config location, because the repos
    # config location is automatically sent to dom0's UpdateVM. Otherwise,
    # we must place the GPG key inside the fedora-30 TemplateVM, then
    # restart sys-firewall.
    - name: /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation
    - source: "salt://sd/sd-workstation/{{ sdvars.signing_key_filename }}"
    - user: root
    - group: root
    - mode: 644

dom0-rpm-test-key-import:
  cmd.run:
    - name: sudo rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation
    - require:
      - file: dom0-rpm-test-key

dom0-workstation-rpm-repo:
  # We use file.managed rather than pkgrepo.managed, because Qubes dom0
  # settings write new repos to /etc/yum.real.repos.d/, but only /etc/yum.repos.d/
  # is copied to the UpdateVM for fetching dom0 packages.
  file.managed:
    - name: /etc/yum.repos.d/securedrop-workstation-dom0.repo
    - user: root
    - group: root
    - mode: 644
    - contents: |
        [securedrop-workstation-dom0]
        gpgcheck=1
        gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation
        enabled=1
        baseurl={{ sdvars.dom0_yum_repo_url }}
        name=SecureDrop Workstation Qubes dom0 repo
    - require:
      - file: dom0-rpm-test-key

dom0-remove-securedrop-workstation-stretch-template:
  pkg.removed:
    - pkgs:
      - qubes-template-securedrop-workstation
    - require:
      - file: dom0-workstation-rpm-repo

dom0-install-securedrop-workstation-template:
  pkg.installed:
    - pkgs:
      - qubes-template-securedrop-workstation-buster
    - require:
      - file: dom0-workstation-rpm-repo
      - pkg: dom0-remove-securedrop-workstation-stretch-template

# Copy script to system location so admins can run ad-hoc
dom0-update-securedrop-script:
  file.managed:
    - name: /usr/bin/securedrop-update
    - source: salt://securedrop-update
    - user: root
    - group: root
    - mode: 755

# Symlink update script into cron, for single point of update
dom0-update-securedrop-script-cron:
  file.symlink:
    - name: /etc/cron.daily/securedrop-update-cron
    - target: /usr/bin/securedrop-update

# Create directory for storing SecureDrop-specific icons
dom0-securedrop-icons-directory:
  file.directory:
    - name: /usr/share/securedrop/icons
    - user: root
    - group: root
    - mode: 755
    - makedirs: True

# Copy SecureDrop icon for use in GUI feedback. It's also present in
# the Salt directory, but the permissions on that dir don't permit
# normal user reads.
dom0-securedrop-icon:
  file.managed:
    - name: /usr/share/securedrop/icons/sd-logo.png
    - source: salt://sd/sd-proxy/logo-small.png
    - user: root
    - group: root
    - mode: 644
    - require:
      - file: dom0-securedrop-icons-directory

dom0-enabled-apparmor-on-whonix-gw-template:
  qvm.vm:
    - name: whonix-gw-15
    - prefs:
      - kernelopts: "nopat apparmor=1 security=apparmor"
    - require:
      - sls: qvm.anon-whonix

dom0-enabled-apparmor-on-whonix-ws-template:
  qvm.vm:
    - name: whonix-ws-15
    - prefs:
      - kernelopts: "nopat apparmor=1 security=apparmor"
    - require:
      - sls: qvm.anon-whonix

dom0-create-opt-securedrop-directory:
  file.directory:
    - name: /opt/securedrop

{% set gui_user = salt['cmd.shell']('groupmems -l -g qubes') %}

dom0-login-autostart-directory:
  file.directory:
    - name: /home/{{ gui_user }}/.config/autostart
    - user: {{ gui_user }}
    - group: {{ gui_user }}
    - mode: 700
    - makedirs: True

dom0-login-autostart-desktop-file:
  file.managed:
    - name: /home/{{ gui_user }}/.config/autostart/SDWLogin.desktop
    - source: "salt://dom0-xfce-desktop-file.j2"
    - template: jinja
    - context:
        desktop_name: SDWLogin
        desktop_comment: Updates SecureDrop Workstation DispVMs at login
        desktop_exec: /usr/bin/securedrop-login
    - user: {{ gui_user }}
    - group: {{ gui_user }}
    - mode: 664
    - require:
      - file: dom0-login-autostart-directory

dom0-login-autostart-script:
  file.managed:
    - name: /usr/bin/securedrop-login
    - source: "salt://securedrop-login"
    - user: root
    - group: root
    - mode: 755

dom0-tag-whonix-ws-15:
  qvm.vm:
    - name: whonix-ws-15
    - tags:
      - add:
        - sd-workstation-updates

dom0-tag-whonix-gw-15:
  qvm.vm:
    - name: whonix-gw-15
    - tags:
      - add:
        - sd-workstation-updates

dom0-securedrop-launcher-directory:
  file.recurse:
    - name: /opt/securedrop/launcher
    - source: "salt://launcher"
    - user: root
    - group: root
    - file_mode: 644
    - dir_mode: 755

dom0-securedrop-launcher-entrypoint-executable:
  file.managed:
    - name: /opt/securedrop/launcher/sdw-launcher.py
    - user: root
    - group: root
    - mode: 755
    - replace: false

dom0-securedrop-launcher-desktop-shortcut:
  file.managed:
    - name: /home/{{ gui_user }}/Desktop/securedrop-launcher.desktop
    - source: "salt://securedrop-launcher.desktop"
    - user: {{ gui_user }}
    - group: {{ gui_user }}
    - mode: 755

{% import_json "sd/config.json" as d %}
{% if d.target != "dev" %}

dom0-install-securedrop-workstation-dom0-config:
  pkg.installed:
    - pkgs:
      - securedrop-workstation-dom0-config
    - require:
      - file: dom0-workstation-rpm-repo

{% endif %}
