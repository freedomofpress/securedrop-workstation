#!/usr/bin/python3
import argparse
import subprocess
from jinja2 import Template

from qubesdb import QubesDB


def get_env(args):
    env = {}
    try:
        db = QubesDB()
        for key in args or []:
            value = db.read(f"/vm-config/{key}")
            if not value or len(value) == 0:
                raise KeyError(f"Could not read from QubesDB: {key}")

    finally:
        db.close()

    return env


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Use -k/--key one or more times to read the specified key from QubesDB.  The input template will be written to the output file with those variables substituted."
    )
    parser.add_argument("-k", "--key", action="append")
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()
    env = get_env(args.key)

    with open(args.input) as input_f:
        template = Template(input_f.read())

    with open(args.output, "w") as output_f:
        rendered = template.render(**env)
        output_f.write(rendered)
