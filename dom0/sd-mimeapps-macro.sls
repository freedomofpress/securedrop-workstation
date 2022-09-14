{% macro link_mimeapps(target) %}

sd-private-volume-mimeapps-handling:
  file.symlink:
    - name: /home/user/.local/share/applications/mimeapps.list
    - target: /opt/sdw/mimeapps.list.{{ target }}
    - user: user
    - group: user
    - require:
      - file: sd-private-volume-mimeapps-config-dir

{% endmacro %}
