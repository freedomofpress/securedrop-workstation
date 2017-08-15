#!/bin/bash

qvm-shutdown sd-gpg
qvm-remove sd-gpg

qvm-shutdown sd-svs
qvm-remove sd-svs

qvm-shutdown sd-whonix
qvm-remove sd-whonix

qvm-shutdown sd-journalist
qvm-remove sd-journalist

qvm-shutdown fedora-23-sd-dispvm-dvm
qvm -remove fedora-23-sd-dispvm-dvm

qvm-shutdown fedora-23-sd-dispvm
qvm-remove fedora-23-sd-dispvm
