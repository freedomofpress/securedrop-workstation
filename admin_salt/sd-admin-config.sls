# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Minimal config for sd-admin, decoupled from securedrop_salt/sd-default-config.sls
# during prototyping. The main SDW config imports config.json (which contains
# SDW-specific fields like submission_key_fpr and vmsizes) and hardcodes
# distribution=bookworm. We hardcode trixie here instead.
#
# TODO: Post-spike, consider extracting shared apt config into a common location
# to avoid duplication with securedrop_salt/sd-default-config.sls.
##

{% set admin_vars = {
    "apt_sources_filename": "apt_freedom_press.sources",
    "component": "main",
    "distribution": "trixie"
} %}
