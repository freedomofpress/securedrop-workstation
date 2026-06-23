# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# TODO: parametrise this
{% if grains['id'] in ["sd-small-debian-13", "sd-large-debian-13"] %}
include:
  - securedrop_salt.fpf-apt-repo

# Install securedrop-log package in TemplateVMs only
install-securedrop-log-package:
  pkg.installed:
    - pkgs:
      - securedrop-log
    - require:
      - sls: securedrop_salt.fpf-apt-repo

{% endif %}

{% if grains['id'] == "sd-small-debian-{}".format(grains['osrelease']) %}
install-redis-for-sd-log-template:
  pkg.installed:
    - pkgs:
      - redis-server
      - redis

{% endif %}
