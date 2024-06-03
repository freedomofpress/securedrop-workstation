# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Installs dom0 config scripts specific to tracking updates
# over time. These scripts should be ported to an RPM package.
##

# Imports "sdvars" for environment config
{% from 'securedrop_salt/sd-default-config.sls' import sdvars with context %}

dom0-rpm-test-key:
  file.managed:
    # We write the pubkey to the repos config location, because the repos
    # config location is automatically sent to dom0's UpdateVM. Otherwise,
    # we must place the GPG key inside the fedora TemplateVM, then
    # restart sys-firewall.
    - name: /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation
    - source: "salt://securedrop_salt/{{ sdvars.signing_key_filename }}"
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
        skip_if_unavailable=False
        gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation
        enabled=1
        baseurl={{ sdvars.dom0_yum_repo_url }}
        name=SecureDrop Workstation Qubes dom0 repo
    - require:
      - file: dom0-rpm-test-key

# Ensure debian-12-minimal is present for use as base template
dom0-install-debian-minimal-template:
  cmd.run:
    - name: >
        qvm-template info --machine-readable debian-12-minimal | grep -q "installed|debian-12-minimal|" || qvm-template install debian-12-minimal

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
    - name: /home/{{ gui_user }}/.config/autostart/press.freedom.SecureDropUpdater.desktop
    - source: "salt://securedrop_salt/dom0-xfce-desktop-file.j2"
    - template: jinja
    - context:
        desktop_name: SDWLogin
        desktop_comment: Updates SecureDrop Workstation DispVMs at login
        desktop_exec: /usr/bin/sdw-login
    - user: {{ gui_user }}
    - group: {{ gui_user }}
    - mode: 664
    - require:
      - file: dom0-login-autostart-directory

dom0-securedrop-launcher-desktop-shortcut:
  file.managed:
    - name: /home/{{ gui_user }}/Desktop/press.freedom.SecureDropUpdater.desktop
    - source: "salt://securedrop_salt/press.freedom.SecureDropUpdater.desktop"
    - user: {{ gui_user }}
    - group: {{ gui_user }}
    - mode: 755

{% import_json "securedrop_salt/config.json" as d %}
{% if d.environment != "dev" %}
# In the dev environment, we've already installed the rpm from
# local sources, so don't also pull in from the yum-test repo.
dom0-install-securedrop-workstation-dom0-config:
  pkg.installed:
    - pkgs:
      - securedrop-workstation-dom0-config
    - require:
      - file: dom0-workstation-rpm-repo
{% endif %}

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
