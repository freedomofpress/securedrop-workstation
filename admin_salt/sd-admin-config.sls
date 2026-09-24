# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# APT config for sd-admin

{% import_json "admin_salt/config.json" as d %}

# Respect "dev" and "staging" envs if provided, default to "prod"
{% if d.environment == "dev" %}
  # use apt-test and nightlies
  {% set admin_vars = {
      "apt_sources_filename": "apt-test_freedom_press.sources",
      "component": "main nightlies",
  } %}
{% elif d.environment == "staging" %}
  # use apt-test and main (RC/test builds)
  {% set admin_vars = {
      "apt_sources_filename": "apt-test_freedom_press.sources",
      "component": "main",
  } %}
{% else %}
  {% set admin_vars = {
      "apt_sources_filename": "apt_freedom_press.sources",
      "component": "main",
  } %}
{% endif %}

{% set _ = admin_vars.update({"distribution": "trixie"}) %}
