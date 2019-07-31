# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Installs dom0 config scripts specific to tracking updates
# over time. These scripts should be ported to an RPM package.
##

dom0-rpm-test-key:
  file.managed:
    # We write the pubkey to the repos config location, because the repos
    # config location is automatically sent to dom0's UpdateVM. Otherwise,
    # we must place the GPG key inside the fedora-29 TemplateVM, then
    # restart sys-firewall.
    - name: /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test
    - source: "salt://sd/sd-workstation/apt-test-pubkey.asc"
    - user: root
    - group: root
    - mode: 644

dom0-rpm-test-key-import:
  cmd.run:
    - name: sudo rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test
    - require:
      - file: dom0-rpm-test-key

dom0-rpm-test-key-sys-firewall:
  cmd.run:
    # Pass in the pubkey directly to sys-firewall, so it's available on the
    # UpdateVM for dom0 while we're configuring dom0 repos.
    - name: >
        qvm-run -p sys-firewall '
        sudo tee /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test'
        < /srv/salt/sd/sd-workstation/apt-test-pubkey.asc

dom0-rpm-test-key-sys-firewall-import:
  cmd.run:
    - name: >
        qvm-run --no-gui sys-firewall '
        sudo rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test'
    - require:
      - cmd: dom0-rpm-test-key-sys-firewall

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
        gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test
        enabled=1
        baseurl=https://dev-bin.ops.securedrop.org/dom0-rpm-repo/
        name=SecureDrop Workstation Qubes dom0 repo
    - require:
      - file: dom0-rpm-test-key

dom0-install-securedrop-workstation-template:
  pkg.installed:
    - pkgs:
      - qubes-template-securedrop-workstation
    - require:
      - file: dom0-workstation-rpm-repo
      - cmd: dom0-rpm-test-key-sys-firewall

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

# Install latest templates required for SDW VMs.
dom0-install-fedora-29-template:
  pkg.installed:
    - pkgs:
      - qubes-template-fedora-29

dom0-enabled-apparmor-on-whonix-gw-15-template:
  qvm.vm:
    - name: whonix-gw-15
    - prefs:
      - kernelopts: "nopat apparmor=1 security=apparmor"

dom0-enabled-apparmor-on-whonix-ws-15-template:
  qvm.vm:
    - name: whonix-ws-15
    - prefs:
      - kernelopts: "nopat apparmor=1 security=apparmor"

dom0-create-opt-securedrop-directory:
  file.directory:
    - name: /opt/securedrop

