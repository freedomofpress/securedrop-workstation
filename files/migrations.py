#!/usr/bin/python3
"""
Runs migration scripts for this project

Intended to be triggered by the %post rpm scriptlet rather than manually.
"""

import logging
import shutil
import sys
import tempfile
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from typing import List

from migration_steps import MigrationStep


class Version:
    """
    A sortable software version

    Reads version strings, and sorts by major.minor.patch[.etc[.etc …]]
    """

    def __init__(self, version: str) -> None:
        """
        Read version numbers into lists of ints, discard anything that comes
        after the first character that is neither a period nor a digit
        """
        chunks = []
        for part in version.split("."):
            digits = ""
            for char in part:
                if char.isdigit():
                    digits += char
                else:
                    # Treat RCs, betas etc. as if it were the full release
                    break
            chunks.append(int(digits))
        self.version = tuple(chunks)

    def __str__(self) -> str:
        return ".".join(str(v) for v in self.version)


class Migration:
    """
    A runnable migration with a target version
    """

    def __init__(self, path: Path) -> None:
        self.target = Version(path.name.rsplit(".", 1)[0])
        self.path = path

    def run_and_update_version_file(self, version_file: Path) -> None:
        """
        Run this migration
        """

        try:
            loader = SourceFileLoader("migration", str(self.path))
            spec = spec_from_loader("migration", loader)
            assert spec is not None
            migration = module_from_spec(spec)
            loader.exec_module(migration)
        except Exception:
            logging.exception(f"Failed to load migration: {self.path}")
            sys.exit(4)

        logging.info(f"Running migration for {self}")
        migrate(migration.steps)

        # If we successfully ran the migration, we are now in a new state that we want to see
        # reflected in case a subsequent migration fails
        update_version(self.target, version_file)


def update_version(target: Version, version_file: Path) -> None:
    version_file.write_text(f"{target}")


def rollback_steps(steps: List[MigrationStep], failed_index: int, tmpdir_parent: Path) -> None:
    for index, step in reversed(list(enumerate(steps[:failed_index]))):
        try:
            step.rollback(step.tmpdir(tmpdir_parent, index))
        except Exception:
            logging.exception(f"Failed to roll back step {index}: {step}")


def validate(steps: List[MigrationStep]) -> None:
    # Before attempting to run anything, ensure that the required state is met
    for index, step in enumerate(steps):
        try:
            if not step.validate():
                logging.error(f"Failed to validate step {index}: {step}")
                sys.exit(5)
        except Exception:
            logging.exception(f"Encountered error during validation step {index}: {step}")
            sys.exit(5)


def snapshot(steps: List[MigrationStep], tmpdir_parent: Path) -> None:
    for index, step in enumerate(steps):
        tmpdir = step.tmpdir(tmpdir_parent, index)
        tmpdir.mkdir()
        try:
            step.snapshot(tmpdir)
        except Exception:
            logging.exception(f"Failed to snapshot step {index}: {step}")
            sys.exit(6)


def cleanup(steps: List[MigrationStep], tmpdir_parent: Path) -> None:
    # Snapshotting large files or VMs is not always feasible. To avoid destructive actions, they may
    # be renamed but left "in place" instead. This allows rollback, but necessitates a separate
    # cleanup step.
    for index, step in reversed(list(enumerate(steps))):
        try:
            step.cleanup(step.tmpdir(tmpdir_parent, index))
        # Cleanups may fail, but then should not conflict with the desired state of the migration.
        # We do however want to know how they failed, if they failed.
        except Exception:
            logging.exception(f"Failed to clean up step {index}: {step}")
    shutil.rmtree(tmpdir_parent)


def migrate(steps: List[MigrationStep]) -> None:
    with tempfile.TemporaryDirectory(prefix="updater-migrations") as tmpdir:
        tmpdir_parent = Path(tmpdir)
        validate(steps)
        snapshot(steps, tmpdir_parent)

        for index, step in enumerate(steps):
            try:
                logging.info(f"Running: {step}")
                step.run()
            except Exception:
                logging.exception(f"Failed to run migration step {index}: {step}")
                logging.error("Rolling back preceding steps")
                rollback_steps(steps, index, tmpdir_parent)
                sys.exit(2)

        cleanup(steps, tmpdir_parent)


def main(version_file: Path, migrations_dir: Path, action: int, version_target: Version) -> None:
    """
    Migration main entry point

    Either:
    - returns successfully
    - aborts with returncode 2 if there's been a problem while running migration steps
    - aborts with returncode 3 if action is UPGRADE but version_file does not exist
    - aborts with returncode 4 if a given migration is not a valid Python module
    - aborts with returncode 5 if a migration step could not be validated or it encountered an error
      during validation
    - aborts with returncode 6 if an error is enounctered during snapshotting
    """
    version_base = None
    if version_file.exists():
        version_base = Version(version_file.read_text().strip())

        # The following glob implies that no Python file names in this folder may end in a number
        # except migrations named after the version of the state that they establish.
        migrations = sorted(
            [Migration(path) for path in migrations_dir.glob("*[0-9].py")],
            key=lambda migration: migration.target.version,
        )

        for migration in migrations:
            if version_base.version < migration.target.version <= version_target.version:
                migration.run_and_update_version_file(version_file)
    # action: 1: install, 2: upgrade
    elif action == 2:
        # See https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax
        logging.error(f"Aborting: cannot upgrade without version file: '{version_file}'")
        sys.exit(3)

    # If we're installing or if all migrations ran successfully, we can set the target version
    update_version(version_target, version_file)
    logging.info(f"Successfully upgraded to {version_target}")


if __name__ == "__main__":  # pragma: no cover
    PROJECT = sys.argv[1]
    logging.basicConfig(filename=f"/var/log/{PROJECT}-migrations.log", level=logging.INFO)
    main(
        Path(f"/var/lib/{PROJECT}/version"),
        Path(f"/usr/libexec/{PROJECT}/migrations/"),
        int(sys.argv[2]),
        Version(sys.argv[3]),
    )
