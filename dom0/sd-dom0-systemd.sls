# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
##
# Updates to systemd configuration in dom0
##

{% import_json "sd/config.json" as d %}
{% if d.environment == "prod" or d.environment == "staging" %}
# Power off instead of suspend on lid close, for security reasons, but only in
# prod and staging, to avoid interfering with developer workflows
dom0-poweroff:
  file.blockreplace:
    - name: /etc/systemd/logind.conf
    - append_if_not_found: True
    - marker_start: "### BEGIN securedrop-workstation ###"
    - marker_end: "### END securedrop-workstation ###"
    - content: |
        HandleLidSwitch=poweroff

apply-systemd-changes:
  cmd.run:
    - name: sudo systemctl restart systemd-logind
{% endif %}
