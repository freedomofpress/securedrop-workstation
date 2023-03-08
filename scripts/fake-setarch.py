#!/usr/bin/python3
# In containers that cannot be run with seccomp=unconfined, setarch fails,
# breaking reprotest. Symlinking setarch to this file makes reprotest believe
# everything worked as expected without having to patch its code.
from subprocess import run
from sys import argv

if "sh" in argv:
    run(argv[argv.index("sh") :])
