# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Installs dom0 config scripts specific to tracking updates
# over time. These scripts should be ported to an RPM package.
##

# Imports "sdvars" for environment config
{% from 'sd-default-config.sls' import sdvars with context %}

dom0-rpm-test-key:
  file.managed:
    # We write the pubkey to the repos config location, because the repos
    # config location is automatically sent to dom0's UpdateVM. Otherwise,
    # we must place the GPG key inside the fedora TemplateVM, then
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

dom0-workstation-templates-repo:
  # Using file.blockreplace because /etc/qubes/repo-templates/ is not a .d
  # style directory, and qvm.template_installed:fromrepo seems to only support
  # using a repo from this file. Installing manually via a cli-command-instead?
  file.blockreplace:
    - name: /etc/qubes/repo-templates/qubes-templates.repo
    - append_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        [securedrop-workstation-templates]
        gpgcheck=1
        gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation
        enabled=1
        baseurl={{ sdvars.dom0_yum_repo_url }}
        name=SecureDrop Workstation Templates repository
    - require:
      - file: dom0-rpm-test-key

dom0-install-securedrop-workstation-template:
  cmd.run:
    - name: >
        qvm-template info --machine-readable securedrop-workstation-{{ sdvars.distribution }} | grep -q "installed|securedrop-workstation-{{ sdvars.distribution }}|" || qvm-template install securedrop-workstation-{{ sdvars.distribution }}
    - require:
      - file: dom0-workstation-rpm-repo

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
    - source: salt://sd/sd-workstation/logo-small.png
    - user: root
    - group: root
    - mode: 644
    - require:
      - file: dom0-securedrop-icons-directory

dom0-create-opt-securedrop-directory:
  file.directory:
    - name: /opt/securedrop

{% set gui_user = salt['cmd.shell']('groupmems -l -g qubes') %}

# Increase the default icon size for the GUI user for usability/accessibility reasons
dom0-adjust-desktop-icon-size-xfce:
  cmd.script:
    - name: salt://update-xfce-settings
    - args: adjust-icon-size
    - runas: {{ gui_user }}

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

dom0-securedrop-launcher-executables:
  file.managed:
    - names:
      - /opt/securedrop/launcher/sdw-launcher.py
      - /opt/securedrop/launcher/sdw-notify.py
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

# Hide suspend/hibernate options in menus in prod systems
{% if d.environment == "prod" or d.environment == "staging" %}
dom0-disable-unsafe-power-management-xfce:
  cmd.script:
    - name: salt://update-xfce-settings
    - args: disable-unsafe-power-management
    - runas: {{ gui_user }}
{% endif %}
