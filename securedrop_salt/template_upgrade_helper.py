#!/usr/bin/python3
"""
Temporarily prevents startup of managed qubes

Necessary during provisioning, particularly in template changes, where
all qubes dependent on a template (including disposables only
indirectly based on it) need to be shut down, otherwise provisioning fails.

NOTE: deferred template changes may make this redundant
https://github.com/qubesos/qubes-issues/issues/8070
"""

import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

import qubesadmin

from sdw_updater.Updater import DEBIAN_VERSION

# Logging set up
log = logging.getLogger(Path(__file__).name)

PROHIBIT_START_REASON = "SDW: disabled during set up"

# If the script gets abruptly executed at the right point we may loose
# the actual number of disposable VMs. Either that or it was never set
# for some unexplicable circumstance. Since 32GB is the recommended RAM
# having 2 as the default (in case of breakage) it should be acceptable.
SANE_N_DISPVMS = "2"

# qubes-feature name to temporarily hold the number of preloeaded disposables
PRELOAD_MAX_TMP_FEAT_NAME = "preload-dispvm-max-saved"

app = qubesadmin.Qubes()


def start_template_upgrade() -> None:
    """
    Temporarily prevents startup of managed qubes

    Necessary during provisioning, particularly in template changes, where
    all qubes dependent on a template (including disposables only
    indirectly based on it) need to be shut down, otherwise provisioning fails.

    NOTE: deferred template changes may make this redundant
    https://github.com/qubesos/qubes-issues/issues/8070
    """
    # Exclude:
    #   - the ones already with prohibit-start for unrelated reason
    #   - preloaded disposables
    affected_qubes = [
        q
        for q in app.domains
        if (
            "sd-workstation" in q.tags
            and "prohibit-start" not in q.features
            and not getattr(q, "is_preload", False)
        )
    ]

    log.info(
        "Temporarily disabling startup for managed qubes: "
        + ",".join([q.name for q in affected_qubes])
    )
    for qube in affected_qubes:
        qube.features["prohibit-start"] = PROHIBIT_START_REASON

    # Use of qvm-shutdown since it can somewhat handle dependencies
    shutdown_list = [q.name for q in affected_qubes]
    if shutdown_list:
        try:
            subprocess.run(["qvm-shutdown", "--wait", "--"] + shutdown_list, check=True)
        except subprocess.CalledProcessError:
            # Some qubes may take too long to shut down. See
            # https://github.com/freedomofpress/securedrop-workstation/issues/1751
            stubborn_qubes = [q.name for q in affected_qubes if not q.is_halted()]
            log.debug(f"Killing stubborn qubes: {stubborn_qubes}")
            subprocess.run(["qvm-kill", "--"] + stubborn_qubes, check=True)


def finish_template_upgrade() -> None:
    log.info("Re-enabling startup for managed qubes.")

    # Obtain the list again since:
    #  - some qubes may have been removed (e.g. old templates)
    #  - some cloned qubes may have inherited prohibit-startup
    for qube in app.domains:
        if qube.features.get("prohibit-start") == PROHIBIT_START_REASON:
            del qube.features["prohibit-start"]


def template_upgrades_needed() -> bool:
    # NOTE: a more clever detection is warranted, but inspecting what salt is going
    # to do is not a particular thing salt is good at. This is left here for when
    # re-implemented with another IaC tool that doesn't need wrapper scripts like these.
    templ_current_version_checks = [
        q.features["os-version"] == DEBIAN_VERSION
        for q in app.domains
        if ("sd-workstation" in q.tags and q.klass == "TemplateVM")
    ]

    # Ignore if all templates are using the intended version
    is_needed = not all(templ_current_version_checks)

    log.debug(f"Upgrade templates: {is_needed}")
    return is_needed


def start_suppress_preloaded_disposables() -> None:
    """
    Temporarily disable preloaded disposables during provisioning

    This is necessary due to the risk due to a race due to preloaded disposables starting right
    after there's a template switch, but failing to, due to their dvm template having
    prohibit-start. This would leave unstarted 'dispXXXX' on disk with 'sd-workstation' tags but
    that don't report as being preloaded.
    """
    log.info("Temporarily disabling preloaded disposables")
    dom0 = app.domains["dom0"]

    # Save current settings (use dom0 features as way to save state)
    dom0.features[PRELOAD_MAX_TMP_FEAT_NAME] = dom0.features.get(
        "preload-dispvm-max", SANE_N_DISPVMS
    )

    # Disable preloaded disposables (they will start shutting down immediately)
    dom0.features["preload-dispvm-max"] = "0"

    # Wait for preload disposables to shut down
    for attempt in range(1, 11):
        if not any([q for q in app.domains if getattr(q, "is_preload", False)]):
            break

        log.debug("Waiting for preloaded disposables to shut down...")
        time.sleep(3)


def finish_suppress_preloaded_disposables() -> None:
    """
    Re-enable preloaded disposable qubes

    NOTE: this must be safe to run even if start did not run (in case of partial failure)
    """
    log.info("Re-enabling preloaded disposables")
    dom0 = app.domains["dom0"]

    # Reset to original settings
    dom0.features["preload-dispvm-max"] = dom0.features.get(
        PRELOAD_MAX_TMP_FEAT_NAME, SANE_N_DISPVMS
    )
    if dom0.features.get(PRELOAD_MAX_TMP_FEAT_NAME) is None:
        del dom0.features[PRELOAD_MAX_TMP_FEAT_NAME]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "finish"])
    parser.add_argument("--debug", "-d", action="store_true", help="enable debug output")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.action == "start":
        if template_upgrades_needed():
            start_suppress_preloaded_disposables()
            start_template_upgrade()
        else:
            log.info("Template upgrade not necessary")
    elif args.action == "finish":
        finish_template_upgrade()
        finish_suppress_preloaded_disposables()


if __name__ == "__main__":
    main()
