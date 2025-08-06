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

# Our supported Debian distribution is configured here
{% set _ = apt_config.update({"distribution": "bookworm"}) %}

# Get name of keyring package, get package suffix (-dev, -staging)
# if present, and configure environment based on bootstrap package, defaulting to prod.
# Bail if no keyring package is installed
{% set bootstrap_name = 'securedrop-workstation-keyring' %}
{% set bootstrap_installed = salt['pkg.list_pkgs']().get(package_name, None) %}

{% if bootstrap_installed is none %}
  {% do salt.fail.warn('{} is not installed.'.format(bootstrap_name)) %}
{% endif %}

{% set pkgname_split = installed_package.split('-') %}
{% set env = pkgname_split[-1] if pkgname_split[-1] in environments else 'prod' %}

{% set apt_config = environments.get[env] %}

# Store which environment we are using
{% set _ = apt_config.update({"env": env }) %}
