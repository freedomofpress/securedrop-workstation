import os
import shutil
from pathlib import Path

import pytest

TEST_ROOT = Path(__file__).resolve().parent


def copy_migrations(migration, target_dir):
    migration = TEST_ROOT / "migrations" / f"{migration}.py"
    shutil.copy(migration, target_dir / "0.0.1.py")


@pytest.fixture
def tmp_migrations(tmp_path):
    version_file = tmp_path / "version"
    version_file.open("w").write("0.0.0")
    cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(cwd)


# Same as tmp_success_if_valid just to clarify from fixture names that a failing test may be
# expected
@pytest.fixture
def tmp_success(tmp_migrations):
    copy_migrations("success-if-valid", tmp_migrations)
    yield tmp_migrations


@pytest.fixture
def tmp_success_if_valid(tmp_migrations):
    copy_migrations("success-if-valid", tmp_migrations)
    yield tmp_migrations


@pytest.fixture
def tmp_failure(tmp_migrations):
    copy_migrations("failure", tmp_migrations)
    yield tmp_migrations


@pytest.fixture
def tmp_snapshot_failure(tmp_migrations):
    copy_migrations("snapshot-failure", tmp_migrations)
    yield tmp_migrations


@pytest.fixture
def tmp_rollback(tmp_migrations):
    copy_migrations("rollback", tmp_migrations)
    yield tmp_migrations


@pytest.fixture
def tmp_rollback_failure(tmp_migrations):
    copy_migrations("rollback-failure", tmp_migrations)
    yield tmp_migrations


@pytest.fixture
def tmp_cleanup(tmp_migrations):
    copy_migrations("cleanup", tmp_migrations)
    yield tmp_migrations


@pytest.fixture
def tmp_cleanup_failure(tmp_migrations):
    copy_migrations("cleanup-failure", tmp_migrations)
    yield tmp_migrations


def create_file(folder, name="example.txt"):
    fp = folder / name
    fp.open("w").write("Example file to test file operations")
    return fp


def create_alt_folder(folder):
    alt = folder / "different-location"
    alt.mkdir()


@pytest.fixture
def tmp_file(tmp_path):
    create_alt_folder(tmp_path)
    yield create_file(tmp_path)


@pytest.fixture
def tmp_folder(tmp_path):
    folder = tmp_path / "example-folder"
    folder.mkdir()
    create_alt_folder(tmp_path)

    for i in range(3):
        create_file(folder, f"example-{i}.txt")

    yield folder
