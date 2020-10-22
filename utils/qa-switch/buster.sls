remove-prod-apt-repo:
  pkgrepo.absent:
    - name: "deb [arch=amd64] https://apt.freedom.press buster main"

add-test-apt-repo:
  pkgrepo.managed:
    - name: "deb [arch=amd64] https://apt-test.freedom.press buster template-consolidation"
    - file: /etc/apt/sources.list.d/securedrop_workstation.list
    - key_url: "salt://sd/sd-workstation/apt-test-pubkey.asc"
    - clean_file: True
