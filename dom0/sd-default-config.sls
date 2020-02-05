# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
##
# Handles loading of config variables, via environment-specific
# setting in the config file.

# Load YAML vars file
{% load_yaml as sdvars_defaults %}
{% include "sd-default-config.yml" %}
{% endload %}

# Load JSON config file
{% import_json "sd/config.json" as d %}

# Respect "dev" env if provided, default to "prod"
{% if d.environment == "dev" or d.environment == "staging" %}
  {% set sdvars = sdvars_defaults["dev"] %}
{% else %}
  {% set sdvars = sdvars_defaults["prod"] %}
{% endif %}
