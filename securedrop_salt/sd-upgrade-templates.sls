# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

{% import_json "securedrop_salt/config.json" as d %}
{% if d.environment == "dev" %}
  {% set cmd_opts = "--debug" %}
{% else %}
  {% set cmd_opts = "" %}
{% endif %}


run-prep-upgrade-scripts:
  cmd.run:
    - name: /srv/salt/securedrop_salt/template_upgrade_helper.py start {{ cmd_opts }}
    - order: first
    - failhard: True


run-post-upgrade-scripts:
  cmd.run:
    - name: /srv/salt/securedrop_salt/template_upgrade_helper.py finish {{ cmd_opts }}
    - order: last
    - failhard: False  # Ensure this always runs so cleanup happens

