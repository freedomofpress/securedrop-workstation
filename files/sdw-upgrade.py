#!/usr/bin/python3
"""
Interactive assistant for removing deprecated qubes prior to a Qubes OS upgrade.
"""

import argparse
import enum
import logging
import subprocess
import sys
from abc import abstractmethod
from collections import deque

import qubesadmin
import qubesadmin.utils
from qubesadmin.vm import QubesVM

app = qubesadmin.Qubes()

# Logging set up
log = logging.getLogger(__name__)

# ANSI color codes
BOLD = "\033[1m"
CYAN = "\033[36m"
RED = "\033[31m"
ITALIC = "\033[3m"
RESET = "\033[0m"

# Logging-related prefixes
LOG_SUB_ACTION = "--> "
LOG_ACTION = "\n-------> "


def names_to_qubes(qube_names: list[str]) -> list[QubesVM]:
    return [qube for qube_name in qube_names if (qube := app.domains.get(qube_name)) is not None]


def qubes_to_names(qubes_list: list[QubesVM]) -> list[str]:
    return [qube.name for qube in qubes_list]


CURRENT_FEDORA_TEMPLATE = app.domains.get("fedora-43-xfce")

OLD_FEDORA_TEMPLATES = names_to_qubes(
    [
        "fedora-40-xfce",  # Installed with Qubes 4.2.2
        "fedora-41-xfce",  # Installed with Qubes 4.2.3
        "fedora-42-xfce",  # Installed via SDW but not explicitly removed
    ]
)

OLD_FEDORA_DERIVED = names_to_qubes(
    [
        "personal",
        "work",
        "untrusted",
        "vault",
        "default-dvm",
        # NOTE 'default-mgmt-dvm' is SDW-managed and shouldn't be outdated
    ]
)

# Lingering SDW-created fedora disposable templates (see #1523)
OLD_FEDORA_DVMS = names_to_qubes(
    [
        "fedora-40-dvm",
        "fedora-41-dvm",
        # Later qubes are removed by via salt (see commit 63870ef or PR #1638)
    ]
)


class ActionRecommendation(enum.Enum):
    AUTOMATIC = enum.auto()
    MANUAL = enum.auto()
    NOT_NEEDED = enum.auto()


def prompt_user_confirmation(prompt: str) -> bool:
    normalized_response = input(f"{LOG_ACTION}{prompt} [Y/n] ").strip().lower()

    if normalized_response in ("y", "yes"):
        return True
    if normalized_response in ("n", "no"):
        sys.exit(1)
    else:
        print("ERROR: entered response was not recognized. Please try again!")
        return prompt_user_confirmation(prompt)


class UpgradePrepStep:
    def __init__(self, description: str, impact: str) -> None:
        self.description = description  # Short description (imperative form)
        self.impact = impact  # Notes on impact (imperative form)
        self.has_ran = False

    def run(self) -> None:
        """Run step if possible"""
        log.debug(f"On step {type(self).__name__}")
        action = self.can_run()
        if action == ActionRecommendation.AUTOMATIC:
            print(f"{LOG_SUB_ACTION}Applying...")
            self.apply()
            self.has_ran = True
            print(f"{LOG_SUB_ACTION}Successfully applied!")
        elif action == ActionRecommendation.NOT_NEEDED:
            print(f"{LOG_SUB_ACTION}Step skipped (not needed)...")
            self.has_ran = True
        elif action == ActionRecommendation.MANUAL:
            print(f"{ITALIC}Failed to run. Needs to be done manually.{RESET}")

    @abstractmethod
    def can_run(self) -> ActionRecommendation:
        """Checks if pre-conditions are satisfied"""

    @abstractmethod
    def on_fail(self) -> None:
        pass

    @abstractmethod
    def apply(self) -> None:
        """Applies the changes"""


class RemoveQubesStep(UpgradePrepStep):
    def __init__(
        self,
        description: str,
        qubes_for_removal: list[QubesVM],
        expected_dependencies: list[QubesVM] = [],
        impact: str = "(no expected impact on your system)",
    ) -> None:
        # There may not be any existing qubes in which case there's no impact
        if qubes_for_removal or expected_dependencies:
            impact = "It may affect: " + ", ".join(
                qubes_to_names(qubes_for_removal + expected_dependencies)
            )

        super().__init__(description=description, impact=impact)
        self.qubes_for_removal = qubes_for_removal
        self.expected_dependencies = expected_dependencies

        # the qubes affected by removal (incl. removed ones)
        self.impacted_qubes: list[str] = []

    def can_run(self) -> ActionRecommendation:
        """
        Check if purging a list of qubes affects *at most* expected set of qubes

        Traverses the full dependency tree (e.g. networking, inheritance, etc.) and
        check if a purge is generally safe to perform. If there are unknown affected
        qubes it's unsafe for an automated purge.
        """

        # Expected list of affected qubes
        impacted_qubes_expected = set(self.expected_dependencies + self.qubes_for_removal)

        # May be empty if non exist that no longer exist
        if self.qubes_for_removal == []:
            return ActionRecommendation.NOT_NEEDED

        visited = []

        # enqueue "root" dependencies
        queue = deque(self.qubes_for_removal)

        # BFS traversal: to find all dependent qubes
        while queue:
            qube = queue.popleft()

            if qube not in impacted_qubes_expected:
                # early failure: mismatch
                log.debug(f"Unexpected dependent: {qube.name}")
                return ActionRecommendation.MANUAL

            if qube not in visited:
                visited.append(qube)
                for holder_qube, prop in qubesadmin.utils.vm_dependencies(app, qube):
                    if holder_qube is None:
                        # Global properties don't matter for finding dependencies
                        continue

                    queue.append(holder_qube)

        impacted_qubes_real = {
            qube.name
            for qube in visited
            if not getattr(qube, "auto_cleanup", None)  # Ignore disposables
        }
        log.debug(f"impacted_qubes_real: {impacted_qubes_real}")
        log.debug(f"impacted_qubes_expected: {impacted_qubes_expected}")

        # Check if subset (instead of equality) because it's OK if some qubes are
        # no longer affected (e.g. user updated work to be based on latest Fedora)
        if impacted_qubes_real.issubset(set(impacted_qubes_expected)):
            # OK for automated removal. Return affected VMs.
            self.impacted_qubes = list(impacted_qubes_real)
            return ActionRecommendation.AUTOMATIC
        else:
            # This condition should never be reached due to the earlier mismatch exit
            return ActionRecommendation.MANUAL

    def print_purge_impact(
        self,
        removal_text: str = "remove",
        impact_text: str = "affected",
    ) -> None:
        """
        Reports the impact of purging some qubes
        """
        print("\tApplying the following changes:")
        for qube_name in self.impacted_qubes:
            # NOTE: some qubes may not exist. That's why iteration happens over
            # self.impacted_qubes instead of self.qubes_for_removal
            if qube_name in qubes_to_names(self.qubes_for_removal):
                print(f"\t  - {qube_name}\t({removal_text})")
            else:
                print(f"\t  - {qube_name}\t({impact_text})")


class RemoveSD_DVMs(RemoveQubesStep):
    """
    Removes lingering Fedora DVM templates created by SDW
    """

    def __init__(self) -> None:
        super().__init__(
            description="Remove lingering disposables created by SecureDrop Workstation",
            qubes_for_removal=OLD_FEDORA_DVMS,
        )

    def apply(self) -> None:
        self.print_purge_impact()

        # Remove only the qubes that exist
        subprocess.run(["qvm-remove", "--force"] + self.impacted_qubes, check=True)

    def on_fail(self) -> None:
        print(f"\t{BOLD}Action:{RESET} please consider removing: {', '.join(self.impacted_qubes)}")


class RemoveOldFedoras(RemoveQubesStep):
    def __init__(self) -> None:
        super().__init__(
            description="Remove old Fedora templates",
            qubes_for_removal=OLD_FEDORA_TEMPLATES,
            expected_dependencies=OLD_FEDORA_DERIVED,
        )

    def can_run(self) -> ActionRecommendation:
        # NOTE: in practice this is not expected to fail in the upgrade to 4.3,
        # given that it'll be shipped in the same update as the Fedora 43 bump
        if CURRENT_FEDORA_TEMPLATE is None:
            log.debug("fedora-43-xfce not found; cannot reassign derived VMs automatically")
            return ActionRecommendation.MANUAL
        return super().can_run()

    def on_fail(self) -> None:
        old_fedora_template_list = ", ".join(qubes_to_names(self.qubes_for_removal))
        print(
            "\tWe recommend removing Fedora templates. However, we have detected\n"
            "\ta possible non-default configuration that makes it risky for us to\n"
            "\tmodify the system.\n"
        )
        print(
            f"\t{BOLD}Action:{RESET} Please consider removing the following templates manually\n"
            f"\t({old_fedora_template_list}).\n"
        )

    def apply(self) -> None:
        if not CURRENT_FEDORA_TEMPLATE:
            # NOTE: should not be reachable since can_run() validates this
            raise ValueError("Current template does not exist")

        self.print_purge_impact(removal_text="removal", impact_text="upgrade to latest template")

        # Remove templates. Using --disassoc sets dummy in the previously set places
        subprocess.run(
            ["qvm-template", "remove", "--disassoc"] + qubes_to_names(OLD_FEDORA_TEMPLATES),
            check=True,
        )

        # Replace "dummy" and set template as latest fedora
        refreshed_domains = qubesadmin.Qubes().domains
        dummy_qube = refreshed_domains["dummy"]
        for qube in dummy_qube.derived_vms:
            qube.template = CURRENT_FEDORA_TEMPLATE
            print(f"{qube.name}'s template set to {CURRENT_FEDORA_TEMPLATE.name}")

        # Lastly, remove the dummy qube
        print(f"{LOG_SUB_ACTION}Removed temporary 'dummy'")
        subprocess.run(["qvm-remove", "--force", dummy_qube.name], check=True)


class RemoveWhonix17(RemoveQubesStep):
    WHONIX_17_TEMPLATES = names_to_qubes(["whonix-gateway-17", "whonix-workstation-17"])
    WHONIX_17_DERIVED = names_to_qubes(
        [
            "anon-whonix",  # order matters (until we can use "qvm-template purge")
            "whonix-workstation-17-dvm",
            "sys-whonix",
        ]
    )
    WHONIX_17_ALL = WHONIX_17_TEMPLATES + WHONIX_17_DERIVED

    def __init__(self) -> None:
        super().__init__(
            description="Remove Whonix 17 entirely",
            qubes_for_removal=self.WHONIX_17_ALL,
        )

    def apply(self) -> None:
        self.print_purge_impact(removal_text="removal")

        # "qvm-template purge" is best fit but we run into qubes-issues#10879
        subprocess.run(
            ["qvm-remove", "--force"] + qubes_to_names(self.WHONIX_17_DERIVED), check=True
        )
        subprocess.run(
            ["qvm-remove", "--force"] + qubes_to_names(self.WHONIX_17_TEMPLATES), check=True
        )

    def on_fail(self) -> None:
        print("\tWe detected some non-default whonix qubes which made automated risky.")
        print("")
        print(
            f"\t{BOLD}Action:{RESET} Consider removing Whonix 17, if there is no use-case for it."
        )
        print("\tOtherwise, please manually upgrade to Whonix 18.")


def prepare_upgrade() -> None:
    upgrade_prep_steps = [RemoveSD_DVMs(), RemoveOldFedoras(), RemoveWhonix17()]

    # Summary and confirmation
    print(f"\nThe script will {RED}AUTOMATICALLY{RESET} perform the following actions:\n")
    for step_num, step in enumerate(upgrade_prep_steps):
        print(f"  {BOLD}{ITALIC}{step_num+1}. {step.description}{RESET}")
        print(f"    {step.impact}\n")

    print("")
    print(
        f"{BOLD}{RED}WARNING:{RESET} this should only be performed by the system administrator, "
        "since it can lead to unintentional data loss!"
    )

    if prompt_user_confirmation("Please, save your work. Shut down all running qubes?"):
        subprocess.run(["qvm-shutdown", "--wait", "--all"], check=True)

    # Run steps
    for step_num, step in enumerate(upgrade_prep_steps):
        print(f"\n{BOLD}{ITALIC}Step {step_num+1}: {step.description}{RESET}")
        step.run()

    print("\n===================\n\n")

    incomplete_steps = [step for step in upgrade_prep_steps if not step.has_ran]
    if not incomplete_steps:
        print(
            f"{BOLD}{ITALIC}Preparation complete!{RESET} "
            "You are ready to proceed with the Qubes upgrade process!\n"
        )
    else:
        print(
            f"{BOLD}{ITALIC}Some steps failed.{RESET} "
            "You may want to consider doing them manually:\n"
        )

        for incomplete_step in incomplete_steps:
            print(f"{RED}[MANUAL]{RESET} " f"{BOLD}{ITALIC}{incomplete_step.description}{RESET}")
            incomplete_step.on_fail()
            print("")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", "-d", action="store_true", help="enable debug output")
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    try:
        prepare_upgrade()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
