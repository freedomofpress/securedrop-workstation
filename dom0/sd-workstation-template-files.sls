# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
include:
  - fpf-apt-repo

sd-workstation-template-install-kernel-config-packages:
  pkg.installed:
    - pkgs:
      - securedrop-workstation-config
#TODO: flip this back to securedrop-workstation-grsec when packaging changes are complete
      - securedrop-grsec
    - require:
      - sls: fpf-apt-repo

# Ensure that paxctld starts immediately. For AppVMs,
# use qvm.features.enabled = ["paxctld"] to ensure service start.
sd-workstation-template-enable-paxctld:
  service.running:
    - name: paxctld
    - enable: True
    - reload: True
    - require:
      - pkg: sd-workstation-template-install-kernel-config-packages
