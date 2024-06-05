include:
  - securedrop_salt.fpf-apt-repo

install-securedrop-whonix-config:
  pkg.installed:
    - pkgs:
      - securedrop-whonix-config
    - require:
      - sls: securedrop_salt.fpf-apt-repo
