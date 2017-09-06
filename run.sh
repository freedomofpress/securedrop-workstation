#!/bin/bash

### clone fedora-23 template to use as our own dispvm template
echo -e "\e[1;31m Cloning disposable VM template \e[0m"
qvm-clone fedora-23 fedora-23-sd-dispvm

### move salt-related things into place
echo -e "\e[1;31m Moving configurations into place in Dom0... \e[0m"
sudo [ -d /srv/salt/sd/ ] && sudo rm -rf /srv/salt/sd
sudo mkdir /srv/salt/sd

sudo cp config.json /srv/salt/sd
sudo cp sd-journalist.sec /srv/salt/sd
sudo cp -r decrypt /srv/salt/sd
sudo cp -r sd-journalist /srv/salt/sd
sudo cp -r sd-svs /srv/salt/sd

sudo cp dom0/* /srv/salt/

echo -e "\e[1;31m Enabling all VM configurations... \e[0m"

sudo qubesctl top.enable sd-whonix
sudo qubesctl top.enable sd-whonix-hidserv-key
sudo qubesctl top.enable sd-svs
sudo qubesctl top.enable sd-svs-files
sudo qubesctl top.enable sd-journalist
sudo qubesctl top.enable sd-journalist-files
sudo qubesctl top.enable sd-dispvm-files
sudo qubesctl top.enable sd-gpg
sudo qubesctl top.enable sd-gpg-files

echo -e "\e[1;31m Building and configuring Whonix gateway... \e[0m"
sudo qubesctl --targets sd-whonix state.highstate
echo -e "\e[1;31m Building and configuring SVS and journalist AppVMs... \e[0m"
sudo qubesctl --targets sd-svs,sd-gpg,sd-journalist,fedora-23-sd-dispvm state.highstate

# apply salt state
#sudo qubesctl --all state.highstate


echo -e "\e[1;31m Creating disposable VM \e[0m"
qvm-create-default-dvm fedora-23-sd-dispvm
