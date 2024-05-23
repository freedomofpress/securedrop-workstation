install-template-from-qubesdb:
  file.managed:
    - name: /usr/local/bin/template-from-qubesdb
    - source: "salt://template-from-qubesdb.py"
    - mode: 755
