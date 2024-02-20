# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

{% if grains['id'] in ["securedrop-workstation-bullseye", "sd-small-bullseye-template", "sd-large-bullseye-template"] %}
include:
  - fpf-apt-repo

# Install securedrop-log package in TemplateVMs only
install-securedrop-log-package:
  pkg.installed:
    - pkgs:
      - securedrop-log
    - require:
      - sls: fpf-apt-repo

# configure all VMs to send to sd-log - excluded on a per-VM basis below via /rw
configure-rsyslog-for-sd:
  file.managed:
    - name: /etc/sd-rsyslog.conf
    - source: "salt://sd-rsyslog.conf.j2"

{% endif %}

{% if grains['id'] == "sd-small-{}-template".format(grains['oscodename']) %}
install-redis-for-sd-log-template:
  pkg.installed:
    - pkgs:
      - redis-server
      - redis

{% endif %}
