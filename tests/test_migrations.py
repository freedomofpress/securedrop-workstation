# TODO:
# * Unit tests for general purposes steps

import shutil
from pathlib import Path

import pytest

from tests import utils

files_dir = Path(__file__).parent.parent / "files"
# Necessary to be loaded into the PYTHONPATH so that migrations referencing it can be loaded
utils.load_module("migration_steps", files_dir / "migration_steps.py")
migrations = utils.load_module("migrations", files_dir / "migrations.py")


INSTALL = 1
UPGRADE = 2
VERSION_TARGET = migrations.Version("1.1.0")


def _is_missing(path):
    if path.exists():
        assert False


def test_version_double_digits():
    assert migrations.Version("0.0.12").version[2] == 12


def test_version_ignore_intermediary_releases():
    assert migrations.Version("20.0.1-rc5").version == migrations.Version("20.0.1").version


def test_success_install(tmp_success):
    version_file = tmp_success / "version"
    version_file.unlink()
    _is_missing(version_file)

    migrations.main(version_file, tmp_success, INSTALL, VERSION_TARGET)

    assert version_file.open().read() == str(VERSION_TARGET)


def test_success_install_despite_failing_migrations(tmp_failure):
    version_file = tmp_failure / "version"
    version_file.unlink()
    _is_missing(version_file)

    migrations.main(version_file, tmp_failure, INSTALL, VERSION_TARGET)

    assert version_file.open().read() == str(VERSION_TARGET)


def test_success_migrate(tmp_success):
    version_file = tmp_success / "version"
    assert version_file.open().read() == "0.0.0"

    migrations.main(version_file, tmp_success, UPGRADE, VERSION_TARGET)

    example_file = tmp_success / "example-file.txt"
    assert example_file.open().read() == "0.0.1"

    assert version_file.open().read() == str(VERSION_TARGET)


def test_success_migrate_multiple_and_order(tmp_success):
    version_file = tmp_success / "version"
    assert version_file.open().read() == "0.0.0"

    example_file = tmp_success / "example-file.txt"

    for ver, new_migration in [(f"0.0.{i}", tmp_success / f"0.0.{i}.py") for i in range(1, 5)]:
        if not new_migration.exists():
            shutil.copy(tmp_success / "0.0.1.py", new_migration)

        migrations.main(version_file, tmp_success, UPGRADE, migrations.Version(ver))

        example_file = tmp_success / "example-file.txt"
        assert example_file.open().read() == ver

        assert version_file.open().read() == ver


def test_validation_failed_partial_success(tmp_success_if_valid, caplog):
    version_file = tmp_success_if_valid / "version"
    assert version_file.open().read() == "0.0.0"

    # migrations/success-if-valid.py (which is copied to 0.0.1.py) uses the filename's version as a
    # base for its operations, and requires sequential execution. The patch version - 1 having been
    # run before is checked during validation
    shutil.copy(tmp_success_if_valid / "0.0.1.py", tmp_success_if_valid / "0.0.3.py")

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_success_if_valid, UPGRADE, VERSION_TARGET)

    assert exited_e.type == SystemExit
    assert exited_e.value.code == 2

    assert "Failed to validate" in caplog.text

    # The first migration should succeed
    assert version_file.open().read() == "0.0.1"


def test_validation_exception(tmp_failure, caplog):
    version_file = tmp_failure / "version"
    assert version_file.open().read() == "0.0.0"

    shutil.move(tmp_failure / "0.0.1.py", tmp_failure / "0.0.2.py")

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_failure, UPGRADE, VERSION_TARGET)

    assert exited_e.type == SystemExit
    assert exited_e.value.code == 2

    assert "Encountered error during validation" in caplog.text

    assert version_file.open().read() == "0.0.0"


def test_abort_upgrade_without_version_file(tmp_success_if_valid, caplog):
    """Attempting to upgrade without a version file present should abort"""
    # Testing with migrations that should succeed under normal circumstances…
    version_file = tmp_success_if_valid / "version"
    # … but should not when there's no version file
    version_file.unlink()
    _is_missing(version_file)

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_success_if_valid, UPGRADE, VERSION_TARGET)

    assert exited_e.type == SystemExit
    assert exited_e.value.code == 3

    # Because nothing could be run, no version should be established
    _is_missing(version_file)

    assert "cannot upgrade without version file" in caplog.text


def test_failure_target_state_not_established(tmp_failure, caplog):
    """Migrations that fail should not change the version file to the target version"""
    version_file = tmp_failure / "version"
    assert version_file.open().read() == "0.0.0"

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_failure, UPGRADE, VERSION_TARGET)

    assert exited_e.type == SystemExit
    assert exited_e.value.code == 2

    assert "Intentionally failing" in caplog.text

    assert version_file.open().read() != str(VERSION_TARGET)


def test_failure_migration_not_a_python_file(tmp_failure, caplog):
    version_file = tmp_failure / "version"
    assert version_file.open().read() == "0.0.0"

    migration = tmp_failure / "0.0.1.py"
    migration.open("w").write("boom")

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_failure, UPGRADE, VERSION_TARGET)

    assert exited_e.type == SystemExit
    assert exited_e.value.code == 2

    assert "Failed to load migration" in caplog.text

    assert version_file.open().read() == "0.0.0"


def test_rollback_returns_to_expected_state(tmp_rollback, caplog):
    """Migrations that fail should attempt to reestablish the expected state"""
    version_file = tmp_rollback / "version"
    assert version_file.open().read() == "0.0.0"

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_rollback, UPGRADE, VERSION_TARGET)

    assert exited_e.type == SystemExit
    assert exited_e.value.code == 2

    def created(step):
        return tmp_rollback / f"example-rollback-{step}.txt"

    assert not created(1).exists()
    assert not created(2).exists()
    # The third instance of ExampleRollback should create this in the first place, and is configured
    # to not delete this file during rollback so if it was invoked this will fail
    assert not created(3).exists()

    assert "Intentionally failing" in caplog.text

    assert version_file.open().read() != str(VERSION_TARGET)


def test_rollback_tries_all_rollbacks_logs_failures(tmp_rollback_failure, caplog):
    """Even if rollbacks fail, we continue rolling back as best as possible while logging
    failures"""
    version_file = tmp_rollback_failure / "version"
    assert version_file.open().read() == "0.0.0"

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_rollback_failure, UPGRADE, VERSION_TARGET)

    assert exited_e.type == SystemExit
    assert exited_e.value.code == 2

    def created(step):
        return tmp_rollback_failure / f"example-rollback-{step}.txt"

    assert created(1).exists()
    assert created(2).exists()
    # The rollback for the third instance of ExampleRollback should not run as it is listed after an
    # intentionally failing migration step
    assert not created(3).exists()

    assert "Failed to roll back step 1" in caplog.text

    assert version_file.open().read() != str(VERSION_TARGET)


def test_cleanup_success(tmp_cleanup):
    version_file = tmp_cleanup / "version"
    assert version_file.open().read() == "0.0.0"

    migrations.main(version_file, tmp_cleanup, UPGRADE, VERSION_TARGET)

    example_file = tmp_cleanup / "example-cleanup-file.txt"
    assert example_file.open().read() == "This is clean, trust me"

    assert version_file.open().read() == str(VERSION_TARGET)


def test_cleanup_failure_migration_success(tmp_cleanup_failure, caplog):
    version_file = tmp_cleanup_failure / "version"
    assert version_file.open().read() == "0.0.0"

    migrations.main(version_file, tmp_cleanup_failure, UPGRADE, VERSION_TARGET)

    example_file = tmp_cleanup_failure / "example-cleanup-file.txt"
    assert example_file.open().read() == "Clean me up!"

    assert "Failed to clean up step 0" in caplog.text

    assert version_file.open().read() == str(VERSION_TARGET)


def test_snapshot_failure(tmp_snapshot_failure, caplog):
    version_file = tmp_snapshot_failure / "version"
    assert version_file.open().read() == "0.0.0"

    with pytest.raises(SystemExit) as exited_e:
        migrations.main(version_file, tmp_snapshot_failure, UPGRADE, VERSION_TARGET)

    assert exited_e.type == SystemExit
    assert exited_e.value.code == 2

    print(caplog.text)

    assert "Failed to snapshot step 1" in caplog.text

    assert version_file.open().read() != str(VERSION_TARGET)
