# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Installs dom0 config scripts specific to tracking updates
# over time. These scripts should be ported to an RPM package.
##


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

dom0-install-whonix-14-templates:
  pkg.installed:
    - fromrepo: qubes-templates-community
    - pkgs:
      - qubes-template-whonix-gw-14
      - qubes-template-whonix-ws-14

dom0-enabled-apparmor-on-whonix-gw-14-template:
  qvm.vm:
    - name: whonix-gw-14
    - prefs:
      - kernelopts: "nopat apparmor=1 security=apparmor"
    - require:
      - pkg: dom0-install-whonix-14-templates

dom0-enabled-apparmor-on-whonix-ws-14-template:
  qvm.vm:
    - name: whonix-ws-14
    - prefs:
      - kernelopts: "nopat apparmor=1 security=apparmor"
    - require:
      - pkg: dom0-install-whonix-14-templates

dom0-create-opt-securedrop-directory:
  file.directory:
    - name: /opt/securedrop

# Temporary workaround to bootstrap Salt support on target.
dom0-whonix-gw-14-install-python-futures:
  cmd.run:
    - name: >
        test -f /opt/securedrop/whonix-gw-14-python-futures ||
        qvm-run -a whonix-gw-14
        "python -c 'import concurrent.futures' ||
        { sudo apt-get update && sudo apt-get install -qq python-futures ; }" &&
        qvm-shutdown --wait whonix-gw-14 &&
        touch /opt/securedrop/whonix-gw-14-python-futures
    - require:
      - file: dom0-create-opt-securedrop-directory

dom0-whonix-ws-14-install-python-futures:
  cmd.run:
    - name: >
        test -f /opt/securedrop/whonix-ws-14-python-futures ||
        qvm-run -a whonix-ws-14
        "python -c 'import concurrent.futures' ||
        { sudo apt-get update && sudo apt-get install -qq python-futures ; }" &&
        qvm-shutdown --wait whonix-ws-14 &&
        touch /opt/securedrop/whonix-ws-14-python-futures
    - require:
      - file: dom0-create-opt-securedrop-directory
