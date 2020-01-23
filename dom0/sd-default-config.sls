# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# DEBUGGING
{% set sd_env = salt['environ.get']('SECUREDROP_ENV', default='dev') %}
# See references:
#
#   - https://docs.saltstack.com/en/latest/topics/tutorials/states_pt3.html
#


# Example loading taking from Qubes /srv/salt/top.sls

{% load_yaml as sdvars_defaults %}
{% include "sd-default-config.yml" %}
{% endload %}


{% if sd_env == "prod" %}
{% set sdvars = sdvars_defaults['prod'] %}
{% else %}
{% set sdvars = sdvars_defaults['dev'] %}
{% endif %}
