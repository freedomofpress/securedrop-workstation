# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
include:
  - fpf-apt-test-repo

sd-workstation-template-install-config-from-local:
  file.managed:
    - name: /opt/sdw-config.deb
    - source: salt://sd/sd-workstation/securedrop-workstation-config_0.1.5+buster_all.deb
    - mode: 644
  cmd.run:
    - name: apt install -y /opt/sdw-config.deb

sd-workstation-template-install-kernel-config-packages:
  pkg.installed:
    - pkgs:
      - securedrop-workstation-grsec
    - require:
      - sls: fpf-apt-test-repo

# Ensure that paxctld starts immediately. For AppVMs,
# use qvm.features.enabled = ["paxctld"] to ensure service start.
sd-workstation-template-enable-paxctld:
  service.running:
    - name: paxctld
    - enable: True
    - reload: True
    - require:
      - pkg: sd-workstation-template-install-kernel-config-packages
