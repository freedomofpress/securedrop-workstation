# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
##
# Environment-specific configuration based on securedrop-workstation-keyring
# bootstrap package.

# Possible configurations (apt repo components, Debian-based VMs)
{% set environments = {
    'dev': {
        'url': 'https://apt-test.freedom.press',
        'component': 'main nightlies',
        'filename': 'apt-test_freedom_press.sources',
        'keyfile': '/etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test'
    },
    'staging': {
        'url': 'https://apt-test.freedom.press',
        'component': 'main',
        'filename': 'apt-test_freedom_press.sources',
        'keyfile': '/etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation-test'
    },
    'prod': {
        'url': 'https://apt.freedom.press',
        'component': 'main',
        'filename': 'apt_freedom_press.sources',
        'keyfile': '/etc/pki/rpm-gpg/RPM-GPG-KEY-securedrop-workstation'
    }
} %}

# Find all installed keyring packages (prod is always installed)
{% set keyring_name = "securedrop-workstation-keyring" %}
{% set pkgs_installed = salt['pkg.list_pkgs']() | list %}

# Package precedence: dev, staging, prod (default to prod)
{% set env = "prod" %}

{% if keyring_name ~ "-dev" in pkgs_installed %}
  {% set env = "dev" %}
{% elif keyring_name ~ "-staging" in pkgs_installed %}
  {% set env = "staging" %}
{% endif %}

{% set apt_config = environments.get(env) %}

# Store which environment we are using
{% set _ = apt_config.update({"env": env }) %}

# Our supported Debian distribution is configured here
{% set _ = apt_config.update({"distribution": "bookworm"}) %}
