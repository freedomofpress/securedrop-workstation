# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :


configure mimetype support for debian9:
  pkg.installed:
    - pkgs:
      - gvfs-bin
      - libgnomevfs2-bin
