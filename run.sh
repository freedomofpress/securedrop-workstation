#!/bin/bash

### clone fedora-23 template to use as our own dispvm template
qvm-clone fedora-23 fedora-23-sd-dispvm

### move salt-related things into place
sudo [ -d /srv/salt/sd/ ] && sudo rm -rf /srv/salt/sd
sudo mkdir /srv/salt/sd

sudo cp config.json /srv/salt/sd
sudo cp sd-journalist.sec /srv/salt/sd
sudo cp -r decrypt /srv/salt/sd
sudo cp -r sd-journalist /srv/salt/sd
sudo cp -r sd-svs /srv/salt/sd

sudo cp dom0/* /srv/salt/

sudo qubesctl top.enable sd-whonix
sudo qubesctl top.enable sd-svs
sudo qubesctl top.enable sd-svs-files
sudo qubesctl top.enable sd-journalist
sudo qubesctl top.enable sd-journalist-files
sudo qubesctl top.enable sd-whonix-hidserv-key
sudo qubesctl top.enable sd-dispvm-files
sudo qubesctl top.enable sd-gpg
sudo qubesctl top.enable sd-gpg-files

# apply salt state
sudo qubesctl --all state.highstate

qvm-create-default-dvm fedora-23-sd-dispvm
