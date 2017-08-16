#!/bin/bash

qvm-kill sd-gpg
qvm-remove sd-gpg

qvm-kill sd-svs
qvm-remove sd-svs

qvm-kill sd-journalist
qvm-remove sd-journalist

qvm-kill fedora-23-sd-dispvm-dvm
qvm-remove fedora-23-sd-dispvm-dvm

qvm-kill fedora-23-sd-dispvm
qvm-remove fedora-23-sd-dispvm

qvm-kill sd-whonix
qvm-remove sd-whonix
