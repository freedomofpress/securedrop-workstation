include:
  - fpf-apt-repo

install-securedrop-whonix-config:
  pkg.installed:
    - pkgs:
      - securedrop-whonix-config
    - require:
      - sls: fpf-apt-repo
