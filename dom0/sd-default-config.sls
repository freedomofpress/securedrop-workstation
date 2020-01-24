# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :


{% load_yaml as sdvars_defaults %}
{% include "sd-default-config.yml" %}
{% endload %}

{% import_json "sd/config.json" as d %}

{% if d.target == "dev" %}
  {% set sdvars = sdvars_defaults['dev'] %}
{% else %}
  {% set sdvars = sdvars_defaults['prod'] %}
{% endif %}
