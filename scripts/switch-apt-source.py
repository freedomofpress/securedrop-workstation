#!/usr/bin/python3
"""
Switch APT repositories in the Debian templates.

This only switches the /etc/apt/sources.list.d files and does not on
its own change any of the packages, it's expected you'll use the updater
or some other mechanism for that.

Usage:
    ./scripts/switch-apt-source.py [dev|staging|prod]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

CONFIG_JSON = Path("/usr/share/securedrop-workstation-dom0-config/config.json")
SOURCES_DIR = Path(__file__).parent.parent / "securedrop_salt"

OPTIONS = ["dev", "staging", "prod"]
CODENAME = "bookworm"
TEMPLATES = [
    "sd-small-bookworm-template",
    "sd-large-bookworm-template",
]
TEST_COMPONENTS = {
    "dev": "main nightlies",
    "staging": "main",
}

TEST_SOURCES_FILE = "apt-test_freedom_press.sources"
TEST_SOURCES_TEMPLATE = SOURCES_DIR / f"{TEST_SOURCES_FILE}.j2"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Switch apt sources between dev, staging, and prod"
    )
    parser.add_argument(
        "environment",
        choices=OPTIONS,
        help="Target environment (dev, staging, or prod)",
    )
    return parser.parse_args()


def check_dom0():
    """Verify we're running in dom0."""
    hostname = subprocess.check_output(["hostname"], text=True).strip()
    if hostname != "dom0":
        print(f"Error: This script must be run in dom0, not {hostname}", file=sys.stderr)
        sys.exit(1)


def update_config_json(environment):
    """Update the environment field in config.json."""
    # Read existing config as root
    result = subprocess.run(
        ["sudo", "cat", str(CONFIG_JSON)],
        capture_output=True,
        text=True,
        check=True,
    )
    config = json.loads(result.stdout)

    current_env = config["environment"]
    if current_env == environment:
        print(f"Config already set to environment: {environment}")
        return current_env

    config["environment"] = environment

    # Write updated config as root
    config_content = json.dumps(config, indent=2) + "\n"
    subprocess.run(
        ["sudo", "tee", str(CONFIG_JSON)],
        input=config_content,
        text=True,
        stdout=subprocess.DEVNULL,
        check=True,
    )

    print(f"Updated config.json: {current_env} → {environment}")
    return current_env


def render_test_sources_file(component: str) -> str:
    """Emulate jinja2 so we can render sources template."""
    template = TEST_SOURCES_TEMPLATE.read_text()

    # Simple Jinja2 variable substitution
    return template.replace("{{ codename }}", CODENAME).replace("{{ component }}", component)


def shutdown_template(template):
    print(f"  Shutting down {template}...")
    subprocess.check_call(
        ["qvm-shutdown", template],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def update_template_sources(template, environment):
    """Update apt sources in a template VM."""
    test_sources_path = f"/etc/apt/sources.list.d/{TEST_SOURCES_FILE}"

    # Write apt-test sources file
    if environment in ("dev", "staging"):
        sources_content = render_test_sources_file(TEST_COMPONENTS[environment])
        print(f"  Writing {test_sources_path}...")
        proc = subprocess.Popen(
            ["qvm-run", "--pass-io", template, f"sudo tee {test_sources_path} > /dev/null"],
            stdin=subprocess.PIPE,
            text=True,
        )
        proc.communicate(input=sources_content)
        proc.wait()

    # Remove apt-test sources file if we're on prod
    if environment == "prod":
        print(f"  Removing {test_sources_path}...")
        subprocess.check_call(
            ["qvm-run", "--pass-io", template, f"sudo rm -f {test_sources_path}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    print(f"  ✓ Successfully updated {template}")

    shutdown_template(template)


def main():
    """Main entry point."""
    args = parse_args()
    check_dom0()

    print(f"\nSwitching apt sources to: {args.environment}")
    print()

    # Update config.json
    old_env = update_config_json(args.environment)

    # Check if we're moving down environments
    if OPTIONS.index(args.environment) > OPTIONS.index(old_env):
        print(
            f"Warning: moving from {old_env} to {args.environment}, "
            "which may not properly downgrade packages."
        )

    # Start both templates
    print("\nStarting templates...")
    subprocess.check_call(
        ["qvm-start", "--skip-if-running"] + TEMPLATES,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Update templates
    print("\nUpdating templates...")
    for template in TEMPLATES:
        print(f"\n{template}:")
        update_template_sources(template, args.environment)

    print("\n" + "=" * 60)
    print("✓ All templates updated successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
