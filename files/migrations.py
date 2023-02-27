#!/usr/bin/python3
"""
Runs migration scripts for this project

Intended to be triggered by the %post rpm scriptlet rather than manually.
"""

import logging as log
import shutil
import sys
import tempfile
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path


class Version:
    """
    A sortable software version

    Reads version strings, and sorts by major.minor.patch[.etc[.etc …]]
    """

    def __init__(self, version):
        """
        Read version numbers into lists of ints, discard anything that comes
        after the first character that is neither a period or a digit
        """
        chunks = []
        # Opting for minimal code over execution speed
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

    def __str__(self):
        return ".".join(str(v) for v in self.version)


class Migration(Version):
    """
    A sortable runnable migration

    Subclass of Version so that we can sort migrations just as easily as version strings
    """

    def __init__(self, path):
        super().__init__(path.name.rsplit(".", 1)[0])
        self.path = path

    def run_and_update_version_file(self, version_file):
        """
        Run this migration
        """

        try:
            loader = SourceFileLoader("migration", str(self.path))
            spec = spec_from_loader("migration", loader)
            migration = module_from_spec(spec)
            loader.exec_module(migration)
            log.info(f"Running migration for {self}")
            migrate(migration.steps)
        except Exception as error:
            log.error(f"{error}")
            log.error(f"Failed to load migration: {self.path}")
            exit(2)

        # If we successfully ran the migration, we are now in a new state that we want to see
        # reflected in case a subsequent migration fails
        update_version(self, version_file)


def update_version(target, version_file):
    version_file.write_text(f"{target}")


def _rollback_steps(steps, failed_index, tmpdir):
    for i, step in reversed(list(enumerate(steps[:failed_index]))):
        try:
            step.rollback(tmpdir / f"{step.__class__.__name__}{i}")
        except Exception as error:
            log.error(f"{error}")
            log.error(f"Failed to roll back step {i}: {step}")
            pass


def _validate(steps, tmpdir):
    # Before attempting to run anything, ensure that the required state is met
    for i, step in enumerate(steps):
        try:
            if not step.validate():
                log.error(f"Failed to validate step {i}: {step}")
                exit(2)
        except Exception as error:
            log.error(f"{error}")
            log.error(f"Encountered error during validation step {i}: {step}")
            exit(2)


def _snapshot(steps, tmpdir):
    for i, step in enumerate(steps):
        tmpdir_step = tmpdir / f"{step.__class__.__name__}{i}"
        tmpdir_step.mkdir()
        try:
            step.snapshot(tmpdir_step)
        except Exception as error:
            log.error(f"{error}")
            _rollback_steps(steps, i, tmpdir)
            log.error(f"Failed to snapshot step {i}: {step}")
            exit(2)


def _cleanup(steps, tmpdir):
    # Snapshotting large files or VMs is not always feasible. To avoid destructive actions, they may
    # be renamed but left "in place" instead. This allows rollback, but necessitates a separate
    # cleanup step.
    for i, step in reversed(list(enumerate(steps))):
        try:
            step.cleanup(tmpdir)
        # Cleanups may fail, but then should not conflict with the desired state of the migration.
        # We do however want to know how they failed, if they failed.
        except Exception as error:
            log.error(f"{error}")
            log.error(f"Failed to clean up step {i}: {step}")
            pass
    shutil.rmtree(tmpdir)


def migrate(steps):
    with tempfile.TemporaryDirectory(prefix="updater-migrations") as tmpdir:
        tmpdir = Path(tmpdir)
        _validate(steps, tmpdir)
        _snapshot(steps, tmpdir)

        for i, step in enumerate(steps):
            try:
                log.info(f"Running: {step}")
                step.run()
            except Exception as error:
                log.error(f"{error}: Rolling back preceding steps")
                _rollback_steps(steps, i, tmpdir)
                log.error(f"Failed to run migration step {i}: {step}")
                exit(2)

        _cleanup(steps, tmpdir)


def main(version_file, migrations_dir, action, version_target):
    VERSION_BASE = None
    if version_file.exists():
        with version_file.open("r") as version:
            VERSION_BASE = Version(version.read().strip())

        # The following glob implies that no Python file names in this folder may end in a number
        # except migrations named after the version of the state that they establish.
        migrations = sorted(
            [Migration(p) for p in migrations_dir.glob("*[0-9].py")], key=lambda m: m.version
        )

        for migration in migrations:
            if VERSION_BASE.version < migration.version <= version_target.version:
                migration.run_and_update_version_file(version_file)
    # action: 1: install, 2: upgrade
    elif action == 2:
        # See https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/#_syntax
        log.error(f"Aborting: cannot upgrade without version file: '{version_file}'")
        sys.exit(3)

    # If we're installing or if all migrations ran successfully, we can set the target version
    update_version(version_target, version_file)
    log.info(f"Successfully upgraded to {version_target}")


if __name__ == "__main__":  # pragma: no cover
    PROJECT = sys.argv[1]
    log.basicConfig(filename=f"/var/log/{PROJECT}-migrations.log", level=log.INFO)
    main(
        Path(f"/var/lib/{PROJECT}/version"),
        Path(f"/usr/libexec/{PROJECT}/migrations/"),
        int(sys.argv[2]),
        Version(sys.argv[3]),
    )
