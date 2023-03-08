import shutil
from pathlib import Path

from tests import utils

files_dir = Path(__file__).parent.parent / "files"
# Necessary to be loaded into the PYTHONPATH so that migrations.py can be loaded successfully
migration_steps = utils.load_module("migration_steps", files_dir / "migration_steps.py")


def test_path_snapshot_file(tmp_file):
    """Tests if snapshots for are successfull for files"""
    tmp_path = tmp_file.parent / "different-location"

    migration_steps.path_snapshot(tmp_file, tmp_path)

    assert (tmp_path / tmp_file.name).exists()


def test_path_snapshot_folder(tmp_folder):
    """Tests if snapshots are successfull for populated folders"""
    tmp_path = tmp_folder.parent / "different-location"

    migration_steps.path_snapshot(tmp_folder, tmp_path)

    assert (tmp_path / tmp_folder.name).exists()


def test_path_validate(tmp_folder):
    """
    Tests if path validation allows us to check for the absence or presence of a path (file and
    folder), as well as always returning true regardless of if a path exists or not when passing
    None
    """
    example = tmp_folder / "example-1.txt"
    assert migration_steps.path_validate(example, True)
    assert migration_steps.path_validate(example, None)
    example.unlink()
    assert migration_steps.path_validate(example, None)
    assert migration_steps.path_validate(example, False)
    assert migration_steps.path_validate(tmp_folder, True)
    assert migration_steps.path_validate(tmp_folder, None)
    shutil.rmtree(tmp_folder)
    assert migration_steps.path_validate(tmp_folder, False)


def test_path_rollback_file(tmp_file):
    """
    Test successful rollback for files

    Creates file, takes a snapshot, removes file, asserts that it doesn't exist, rolls back,
    asserts the file exists again and that the contents are the same.
    """
    tmp_path = tmp_file.parent / "different-location"

    contents = tmp_file.read_text()
    migration_steps.path_snapshot(tmp_file, tmp_path)
    tmp_file.unlink()
    assert not tmp_file.exists()

    migration_steps.path_rollback(tmp_file, tmp_path)
    assert tmp_file.exists()
    assert tmp_file.read_text() == contents


def test_path_rollback_folder(tmp_folder):
    """
    Test successful rollback for populated folders

    Takes a snapshot of a populated folder, recursively removes the folder and its contents, asserts
    that it doesn't exist anymore, rolls back, then checks if the files have been restored to their
    original location.
    """

    tmp_path = tmp_folder.parent / "different-location"

    original_contents = sorted(list(tmp_folder.iterdir()))
    migration_steps.path_snapshot(tmp_folder, tmp_path)
    shutil.rmtree(tmp_folder)
    assert not tmp_folder.exists()

    migration_steps.path_rollback(tmp_folder, tmp_path)
    assert tmp_folder.exists()
    rolled_back_contents = sorted(list(tmp_folder.iterdir()))
    assert rolled_back_contents == original_contents


def test_absent_step_file(tmp_file):
    """
    Tests file removal functionality of migration_step.Absent

    Asserts the file we want to remove exists exists, that the validation step that checks that it
    exists agrees, that it's been removed after the step is run, that thefore the validation that
    ensures the file exists confirms it does not, and that after a rollback that the file has been
    restored
    """
    tmp_path = tmp_file.parent / "different-location"

    assert tmp_file.exists()

    step = migration_steps.Absent(tmp_file, True)
    assert step.validate()
    step.snapshot(tmp_path)
    step.run()

    assert not tmp_file.exists()
    assert not step.validate()

    step.rollback(tmp_path)

    assert tmp_file.exists()


def test_absent_step_file_already_absent(tmp_file):
    """
    Tests that migration_step.Absent is compatible with files that are already absent when
    check_exists=None.

    asserts that the file we are ensuring is absent is already absent, with the validation step not
    requiring that it still exists. Subsequent operations, rollback, run and rollback should not
    raise any errors in this situation.
    """
    tmp_path = tmp_file.parent / "different-location"
    tmp_file.unlink()

    assert not tmp_file.exists()

    step = migration_steps.Absent(tmp_file)
    assert step.validate()
    step.snapshot(tmp_path)
    step.run()
    step.rollback(tmp_path)


def test_absent_step_folder(tmp_folder):
    """
    Tests folder removal functionality of migration_step.Absent

    tmp_folder is prepopulated with 3 files example-[0-2].txt - first we assert that the file
    created last exists, that validation is successful, that after running the step that the folder
    and its contents have been removed. We then roll back, and asser that the folder and its
    contents exists again in their original location.
    """
    tmp_path = tmp_folder.parent / "different-location"

    assert (tmp_folder / "example-2.txt").exists()

    step = migration_steps.Absent(tmp_folder)
    assert step.validate()
    step.snapshot(tmp_path)
    step.run()

    for i in range(3):
        fp = tmp_folder / f"example-{i}.txt"
        assert not fp.exists()
    assert not tmp_folder.exists()

    step.rollback(tmp_path)

    assert tmp_folder.exists()
    for i in range(3):
        fp = tmp_folder / f"example-{i}.txt"
        assert fp.exists()


def test_move_step_file(tmp_file):
    """
    Tests the full functionality of the file moval migration step

    Asserts that validation is successful (the file we are about to move exists), and that after
    running the migration step it does not exist in the old location, but it does exist in the new
    location. Then we roll back, and assert that the old file exists again but the new one does not.
    """
    tmp_path = tmp_file.parent / "different-location"
    new_path = tmp_file.parent / "new-location"
    new_path.mkdir()

    step = migration_steps.Move(tmp_file, new_path / tmp_file.name)
    assert step.validate()
    step.snapshot(tmp_path)
    step.run()

    assert not tmp_file.exists()
    new_path_file = new_path / tmp_file.name
    assert new_path_file.exists()

    step.rollback(tmp_path)

    assert not new_path_file.exists()
    assert tmp_file.exists()


def test_move_step_folder(tmp_folder):
    """
    Tests the full functionality of the folder moval migration step

    Asserts that validation is successful (the folder we are about to move exists), and that after
    running the migration step it does not exist in the old location, but it does exist in the new
    location. Then we roll back, and assert that the old folder exists again but the new one does
    not.
    """
    tmp_path = tmp_folder.parent / "different-location"
    new_path = tmp_folder.parent / "new-location"

    step = migration_steps.Move(tmp_folder, new_path)
    assert step.validate()
    step.snapshot(tmp_path)
    step.run()

    assert not tmp_folder.exists()
    assert new_path.exists()

    step.rollback(tmp_path)

    assert tmp_folder.exists()
    assert not new_path.exists()


def test_symlink_step(tmp_file):
    """
    Tests the full functionality of the symlink migration step

    First asserts that validation is successful (the path we are symlinking to exists), and that
    after running the migration step the new path exists and is a symlink. After rolling back, we
    assert that the new symlink does not exist anymore.
    """
    tmp_path = tmp_file.parent / "different-location"
    new_path = tmp_file.parent / "new-location"
    new_path.mkdir()

    step = migration_steps.Symlink(tmp_file, new_path / tmp_file.name)
    assert step.validate()
    step.snapshot(tmp_path)
    step.run()

    new_file = new_path / tmp_file.name
    assert new_file.exists()
    assert new_file.is_symlink()

    step.rollback(tmp_path)
    assert not new_file.exists()
