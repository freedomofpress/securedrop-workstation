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
    # we must place the GPG key inside the fedora-31 TemplateVM, then
    # restart sys-firewall.
    - name: /etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation
    - source: "salt://sd/sd-workstation/apt-test-pubkey.asc"
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
        baseurl=https://yum-test.securedrop.org/workstation/dom0/f25
        name=SecureDrop Workstation Qubes dom0 repo
    - require:
      - file: dom0-rpm-test-key
