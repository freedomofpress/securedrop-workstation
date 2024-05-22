#!/usr/bin/python3
import argparse
import string

from qubesdb import QubesDB


def get_env(args):
    env = {}
    try:
        db = QubesDB()
        for key in args or []:
            value = db.read(f"/vm-config/{key}")
            if not value or len(value) == 0:
                raise KeyError(f"Could not read from QubesDB: {key}")
            env[key] = (value or "").decode()

    finally:
        db.close()

    return env


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="The input template will be written to the output file, with each variable "
        "replaced by its value from QubesDB.  If any variable cannot be read from QubesDB, "
        "templating will fail.  See the documentation on Python's string.Template for details "
        "(https://docs.python.org/3/library/string.html#template-strings)",
    )
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()

    with open(args.input) as input_f:
        template = string.Template(input_f.read())

    env = get_env(template.get_identifiers())  # type: ignore[attr-defined]

    with open(args.output, "w") as output_f:
        rendered = template.substitute(env)
        output_f.write(rendered)
