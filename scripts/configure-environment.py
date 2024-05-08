#!/usr/bin/python3
"""
Updates the config.json in-place in dom0 to set the environment to 'dev' or
'staging'.
"""

import argparse
import json
import os
import sys


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="config.json",
        required=False,
        action="store",
        help="Path to JSON configuration file",
    )
    parser.add_argument(
        "--environment",
        default="dev",
        required=False,
        action="store",
        help="Target deploy strategy, i.e. 'dev', or 'staging'",
    )
    args = parser.parse_args()
    if not os.path.exists(args.config):
        msg = f"Config file not found: {args.config}\n"
        sys.stderr.write(msg)
        parser.print_help(sys.stderr)
        sys.exit(1)

    if args.environment not in ("dev", "staging"):
        parser.print_help(sys.stderr)
        sys.exit(2)
    return args


def set_env_in_config(args):
    with open(args.config) as f:
        old_config = json.load(f)

    new_config = dict(old_config)
    new_config["environment"] = args.environment

    if new_config != old_config:
        msg = f"Updated config environment to '{args.environment}'...\n"
        sys.stderr.write(msg)

        with open(args.config, "w") as f:
            json.dump(new_config, f)


if __name__ == "__main__":
    args = parse_args()

    set_env_in_config(args)
