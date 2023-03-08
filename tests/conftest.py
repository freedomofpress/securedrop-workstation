import os

import pytest


@pytest.fixture
def tmp_migrations(tmp_path):
    version_file = tmp_path / "version"
    version_file.open("w").write("0.0.0")
    cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(cwd)


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
