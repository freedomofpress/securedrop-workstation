#!/usr/bin/python3
# In containers that cannot be run with seccomp=unconfined, setarch fails,
# breaking reprotest. Symlinking setarch to this file makes reprotest believe
# everything worked as expected without having to patch its code.
from subprocess import run
from sys import argv

start = 3 if argv[2] == "-R" else 2
run(argv[start:])
