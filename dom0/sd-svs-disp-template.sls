
sd-svs-disp-template:
  qvm.vm:
    - name: sd-svs-disp-template
    - clone:
      - source: sd-workstation-template
      - label: yellow

install securedrop-workstation-svs-disp in sd-svs-disp-template:
  pkg.installed:
    - pkgs:
      - securedrop-workstation-svs-disp
