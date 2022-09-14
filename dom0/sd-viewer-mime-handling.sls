include:
  - sd-mime-handling

{% from 'sd-mimeapps-macro.sls' import link_mimeapps with context %}

{{ link_mimeapps('sd-viewer') }}
