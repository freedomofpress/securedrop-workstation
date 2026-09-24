#!/usr/bin/python3
"""
Updates the config.json in-place in dom0 to set the environment to 'dev' or
'staging'.

With --admin, only the environment is set in the user's config.json (creating
it if necessary), since the admin workstation doesn't need any other config.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

USER_CONFIG_DIR = Path.home() / ".config/securedrop-manage/"


def parse_args() -> argparse.Namespace:
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
    parser.add_argument(
        "--admin",
        default=False,
        required=False,
        action="store_true",
        help="Configure the admin workstation (ignores --config)",
    )
    args = parser.parse_args()
    if not args.admin and not os.path.exists(args.config):
        msg = f"Config file not found: {args.config}\n"
        sys.stderr.write(msg)
        parser.print_help(sys.stderr)
        sys.exit(1)

    if args.environment not in ("dev", "staging"):
        parser.print_help(sys.stderr)
        sys.exit(2)
    return args


def set_env_in_config(args: argparse.Namespace) -> None:
    with open(args.config) as f:
        old_config = json.load(f)

    new_config = dict(old_config)
    new_config["environment"] = args.environment

    if new_config != old_config:
        msg = f"Updated config environment to '{args.environment}'...\n"
        sys.stderr.write(msg)

        with open(args.config, "w") as f:
            json.dump(new_config, f)


def apply_config(config_path: str) -> None:
    """Copying config secrets into place"""
    config_source = Path(config_path).parent

    user_config_dir = USER_CONFIG_DIR
    salt_config_dir = Path("/srv/salt/securedrop_salt")

    user_config_dir.mkdir(parents=True, exist_ok=True)

    for file in ["config.json", "sd-journalist.sec"]:
        subprocess.run(["cp", "-v", config_source / file, user_config_dir], check=True)
        subprocess.run(["chmod", "ugo+r", user_config_dir / file], check=True)
        subprocess.run(["sudo", "cp", "-v", config_source / file, salt_config_dir], check=True)
        subprocess.run(["sudo", "chmod", "ugo+r", salt_config_dir / file], check=True)


def configure_admin(environment: str) -> None:
    """Set the environment in the user's config.json, which is all the admin workstation needs"""
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_path = USER_CONFIG_DIR / "config.json"
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    if config.get("environment") != environment:
        sys.stderr.write(f"Updated {config_path} environment to '{environment}'...\n")
        config["environment"] = environment
        config_path.write_text(json.dumps(config))


if __name__ == "__main__":
    args = parse_args()

    if args.admin:
        configure_admin(args.environment)
    else:
        set_env_in_config(args)
        apply_config(args.config)
