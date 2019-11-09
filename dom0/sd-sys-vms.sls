


#set-fedora-default-template-version:
#  cmd.run:
#    - name: qubes-prefs default_template fedora-30


{% set sd_supported_fedora_version = 'fedora-30' %}


{% for sys_vm in ['sys-usb', 'sys-net', 'sys-firewall'] %}

{% set sys_vm_template = salt['cmd.shell']('qvm-prefs '+sys_vm+' template') %}

{% if sys_vm_template != sd_supported_fedora_version %}

sd-{{ sys_vm }}-fedora-version-halt:
  qvm.kill:
    - name: {{ sys_vm }}

sd-{{ sys_vm }}-fedora-version-halt-wait:
  cmd.run:
    - name: sleep 5
    - require:
      - qvm: sd-{{ sys_vm }}-fedora-version-halt

sd-{{ sys_vm }}-fedora-version-update:
  qvm.vm:
    - name: {{ sys_vm }}
    - prefs:
      - template: {{ sd_supported_fedora_version }}
    - require:
      - cmd: sd-{{ sys_vm }}-fedora-version-halt-wait

sd-{{ sys_vm }}-fedora-version-start:
  qvm.start:
    - name: {{ sys_vm }}
    - require:
      - qvm: sd-{{ sys_vm }}-fedora-version-update

{% endif %}
{% endfor %}
