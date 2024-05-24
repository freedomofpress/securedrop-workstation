# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
##
# Handles loading of config variables, via environment-specific
# setting in the config file.

# Load YAML vars file
{% load_yaml as sdvars_defaults %}
{% include "securedrop_salt/sd-default-config.yml" %}
{% endload %}

# Load JSON config file
{% import_json "securedrop_salt/config.json" as d %}

# Respect "dev" env if provided, default to "prod"
{% if d.environment == "dev" %}
  # use apt-test and nightlies
  {% set sdvars = sdvars_defaults["test"] %}
  {% set _ = sdvars.update({"component": "main nightlies"}) %}
{% elif d.environment == "staging" %}
  # use apt-test and main (RC/test builds)
  {% set sdvars = sdvars_defaults["test"] %}
  {% set _ = sdvars.update({"component": "main"}) %}
{% else %}
  {% set sdvars = sdvars_defaults["prod"] %}
  {% set _ = sdvars.update({"component": "main"}) %}
{% endif %}

# Append repo URL with appropriate dom0 Fedora version
{% set fedora_repo = "f37" %}
{% set _ = sdvars.update({"distribution": "bookworm"}) %}
{% set _ = sdvars.update({"dom0_yum_repo_url": sdvars["dom0_yum_repo_url"] + fedora_repo}) %}
