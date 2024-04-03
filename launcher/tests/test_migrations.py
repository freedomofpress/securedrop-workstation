from pathlib import Path

import pytest

from tests.utils import copy_migration, load_module

files_dir = Path(__file__).parent.parent / "files"
# Necessary to be loaded into the PYTHONPATH so that migrations referencing it can be loaded
load_module("migration_steps", files_dir / "migration_steps.py")
migrations = load_module("migrations", files_dir / "migrations.py")


INSTALL = 1
UPGRADE = 2
VERSION_TARGET = migrations.Version("1.1.0")


def assert_is_missing(path):
    if path.exists():
        assert False


def test_version_double_digits():
    """The version parser should support multi-digit numbers"""
    assert migrations.Version("0.0.12").version[2] == 12


def test_version_ignore_intermediary_releases():
    """The version parser treats alpha/beta/release candidates as if they were the full version"""
    assert migrations.Version("20.0.1-rc5").version == migrations.Version("20.0.1").version


def test_success_install(tmp_migrations):
    """An installation is successful even if no version file exists, and does not run a
    migration as the package itself should establish the newest state by itself."""
    copy_migration("success-if-valid", tmp_migrations)
    version_file = tmp_migrations / "version"
    version_file.unlink()
    assert_is_missing(version_file)

    migrations.main(version_file, tmp_migrations, INSTALL, VERSION_TARGET)

    # Should not have been created as the migration should not have run
    example_file = tmp_migrations / "example-file.txt"
    assert_is_missing(example_file)
    assert version_file.read_text() == str(VERSION_TARGET)


def test_success_install_despite_failing_migrations(tmp_migrations):
    """An installation is successful even if the migrations it would run would fail"""
    copy_migration("failure", tmp_migrations)
    version_file = tmp_migrations / "version"
    version_file.unlink()
    assert_is_missing(version_file)

    migrations.main(version_file, tmp_migrations, INSTALL, VERSION_TARGET)

    assert version_file.read_text() == str(VERSION_TARGET)


def test_success_migrate(tmp_migrations):
    """A single migration that is expected to be working does indeed work and leaves the system
    state as expected."""
    copy_migration("success-if-valid", tmp_migrations)
    version_file = tmp_migrations / "version"
    assert version_file.read_text() == "0.0.0"

    migrations.main(version_file, tmp_migrations, UPGRADE, VERSION_TARGET)

    example_file = tmp_migrations / "example-file.txt"
    assert example_file.read_text() == "0.0.1"

    assert version_file.read_text() == str(VERSION_TARGET)


def test_success_migrate_multiple_and_order(tmp_migrations):
    """Multiple migrations that that are expected to be working do so and they are executed in the
    expected order."""
    copy_migration("success-if-valid", tmp_migrations)
    version_file = tmp_migrations / "version"
    assert version_file.read_text() == "0.0.0"

    example_file = tmp_migrations / "example-file.txt"

    for version in [f"0.0.{i}" for i in range(1, 5)]:
        migration = tmp_migrations / f"{version}.py"
        if not migration.exists():
            copy_migration("success-if-valid", tmp_migrations, version)

        migrations.main(version_file, tmp_migrations, UPGRADE, migrations.Version(version))

        example_file = tmp_migrations / "example-file.txt"
        assert example_file.read_text() == version

        assert version_file.read_text() == version


def test_validation_failed_partial_success(tmp_migrations, caplog):
    """When we have multiple migrations that we run, the system state reflects the one of the last
    working migration, rather than the original state or the target state."""
    copy_migration("success-if-valid", tmp_migrations)
    version_file = tmp_migrations / "version"
    assert version_file.read_text() == "0.0.0"

    # migrations/success-if-valid.py (which is copied to 0.0.1.py) uses the filename's version as a
    # base for its operations, and requires sequential execution. The patch version - 1 having been
    # run before is checked during validation, so running this file as 0.0.3.py after 0.0.1.py
    # should fail
    copy_migration("success-if-valid", tmp_migrations, "0.0.3")

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_migrations, UPGRADE, VERSION_TARGET)

    # Failed validations have returncode 5
    assert exited_e.value.code == 5

    assert "Failed to validate" in caplog.text

    # The first migration should succeed
    assert version_file.read_text() == "0.0.1"


def test_validation_exception(tmp_migrations, caplog):
    """Treat an exception during validation like failed validation but log the error."""
    copy_migration("validation-failure", tmp_migrations, "0.0.1")
    version_file = tmp_migrations / "version"
    assert version_file.read_text() == "0.0.0"

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_migrations, UPGRADE, VERSION_TARGET)

    # Failures during validation have returncode 5
    assert exited_e.value.code == 5

    assert "Encountered error during validation" in caplog.text

    assert version_file.read_text() == "0.0.0"


def test_abort_upgrade_without_version_file(tmp_migrations, caplog):
    """Attempting to upgrade without a version file present should exit"""
    # Testing with migrations that should succeed under normal circumstances…
    copy_migration("success-if-valid", tmp_migrations)
    version_file = tmp_migrations / "version"
    # … but should not when there's no version file
    version_file.unlink()
    assert_is_missing(version_file)

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_migrations, UPGRADE, VERSION_TARGET)

    # No version file to upgrade from results in exit code 3 instead of 2
    assert exited_e.value.code == 3

    # Because nothing could be run, no version should be established
    assert_is_missing(version_file)

    assert "cannot upgrade without version file" in caplog.text


def test_failure_target_state_not_established(tmp_migrations, caplog):
    """Migrations that fail should not change the version file to the target version"""
    copy_migration("failure", tmp_migrations)
    version_file = tmp_migrations / "version"
    assert version_file.read_text() == "0.0.0"

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_migrations, UPGRADE, VERSION_TARGET)

    # Failing migrations have returncode 2
    assert exited_e.value.code == 2

    assert "Intentionally failing" in caplog.text

    assert version_file.read_text() != str(VERSION_TARGET)


def test_failure_migration_not_a_python_file(tmp_migrations, caplog):
    """If migration files aren't valid Python files, we run the migrations we can and fail in the
    expected manner when encountering the broken file"""
    copy_migration("success-if-valid", tmp_migrations)
    version_file = tmp_migrations / "version"
    assert version_file.read_text() == "0.0.0"

    migration = tmp_migrations / "0.0.2.py"
    migration.write_text("boom")

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_migrations, UPGRADE, VERSION_TARGET)

    # Migrations that cannot be loaded have returncode 4
    assert exited_e.value.code == 4

    assert "Failed to load migration" in caplog.text

    assert version_file.read_text() == "0.0.1"


def test_rollback_returns_to_last_known_good_state(tmp_migrations, caplog):
    """Migrations that fail should attempt to reestablish the last known good state"""
    copy_migration("success-if-valid", tmp_migrations)
    copy_migration("rollback", tmp_migrations, "0.0.2")
    version_file = tmp_migrations / "version"
    assert version_file.read_text() == "0.0.0"

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_migrations, UPGRADE, VERSION_TARGET)

    assert exited_e.value.code == 2

    def created(step):
        return tmp_migrations / f"example-rollback-{step}.txt"

    assert not created(1).exists()
    assert not created(2).exists()
    # After steps 1 and 2, we raise an exception and trigger rollback. The third instance of
    # ExampleRollback would create this file and is configured to not delete this file during
    # rollback so if it was invoked despite the exception this will fail
    assert not created(3).exists()

    assert "Intentionally failing" in caplog.text

    assert version_file.read_text() == "0.0.1"


def test_rollback_tries_all_rollbacks_logs_failures(tmp_migrations, caplog):
    """Even if rollbacks fail, we continue rolling back as best as possible while logging
    failures"""
    copy_migration("success-if-valid", tmp_migrations)
    copy_migration("rollback-failure", tmp_migrations, "0.0.2")
    version_file = tmp_migrations / "version"
    assert version_file.read_text() == "0.0.0"

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_migrations, UPGRADE, VERSION_TARGET)

    assert exited_e.value.code == 2

    def created(step):
        return tmp_migrations / f"example-rollback-{step}.txt"

    assert created(1).exists()
    assert created(2).exists()
    # Same as with test_rollback_returns_to_expected_state, the third instance of ExampleRollback
    # should not run but would leave this file in place if it was
    assert not created(3).exists()

    assert "Failed to roll back step 1" in caplog.text

    assert version_file.read_text() == "0.0.1"


def test_cleanup_success(tmp_migrations):
    """When cleanup operations are available, they are executed"""
    copy_migration("cleanup", tmp_migrations)
    version_file = tmp_migrations / "version"
    assert version_file.read_text() == "0.0.0"

    migrations.main(version_file, tmp_migrations, UPGRADE, VERSION_TARGET)

    example_file = tmp_migrations / "example-cleanup-file.txt"
    assert example_file.read_text() == "This is clean, trust me"

    assert version_file.read_text() == str(VERSION_TARGET)


def test_cleanup_failure_migration_success(tmp_migrations, caplog):
    """If a cleanup operation fails, log the error but do not count this as a failure to execute the
    migration."""
    copy_migration("cleanup-failure", tmp_migrations)
    version_file = tmp_migrations / "version"
    assert version_file.read_text() == "0.0.0"

    migrations.main(version_file, tmp_migrations, UPGRADE, VERSION_TARGET)

    example_file = tmp_migrations / "example-cleanup-file.txt"
    assert example_file.read_text() == "Clean me up!"

    assert "Failed to clean up step 0" in caplog.text

    assert version_file.read_text() == str(VERSION_TARGET)


def test_snapshot_failure(tmp_migrations, caplog):
    """If snapshots fail, count this as a failed migration because we do not want to run potentially
    destructive operations without being able to revert them."""
    copy_migration("snapshot-failure", tmp_migrations)
    version_file = tmp_migrations / "version"
    assert version_file.read_text() == "0.0.0"

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_migrations, UPGRADE, VERSION_TARGET)

    # Failures during snapshotting result in returncode 6
    assert exited_e.value.code == 6

    assert "Failed to snapshot step 1" in caplog.text

    assert version_file.read_text() != str(VERSION_TARGET)
