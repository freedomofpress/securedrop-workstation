import shutil
from pathlib import Path

from tests import utils

files_dir = Path(__file__).parent.parent / "files"
# Necessary to be loaded into the PYTHONPATH so that migrations.py can be loaded successfully
migration_steps = utils.load_module("migration_steps", files_dir / "migration_steps.py")


def test_path_snapshot_file(tmp_file):
    tmp_path = tmp_file.parent / "different-location"

    migration_steps.path_snapshot(tmp_file, tmp_path)

    assert (tmp_path / tmp_file.name).exists()


def test_path_snapshot_folder(tmp_folder):
    tmp_path = tmp_folder.parent / "different-location"

    migration_steps.path_snapshot(tmp_folder, tmp_path)

    assert (tmp_path / tmp_folder.name).exists()


def test_path_validate(tmp_folder):
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
    tmp_path = tmp_file.parent / "different-location"

    contents = tmp_file.open().read()
    migration_steps.path_snapshot(tmp_file, tmp_path)
    tmp_file.unlink()
    assert not tmp_file.exists()

    migration_steps.path_rollback(tmp_file, tmp_path)
    assert tmp_file.exists()
    assert tmp_file.open().read() == contents


def test_path_rollback_folder(tmp_folder):
    tmp_path = tmp_folder.parent / "different-location"

    original_contents = [fp.name for fp in tmp_folder.glob("*")]
    original_contents.sort()
    migration_steps.path_snapshot(tmp_folder, tmp_path)
    shutil.rmtree(tmp_folder)
    assert not tmp_folder.exists()

    migration_steps.path_rollback(tmp_folder, tmp_path)
    assert tmp_folder.exists()
    rolled_back_contents = [fp.name for fp in tmp_folder.glob("*")]
    rolled_back_contents.sort()
    assert rolled_back_contents == original_contents


def test_absent_step_file(tmp_file):
    tmp_path = tmp_file.parent / "different-location"

    assert tmp_file.exists()

    step = migration_steps.Absent(str(tmp_file), True)
    assert step.validate()
    step.snapshot(tmp_path)
    step.run()

    assert not tmp_file.exists()
    assert not step.validate()

    step.rollback(tmp_path)

    assert tmp_file.exists()


def test_absent_step_file_already_absent(tmp_file):
    tmp_path = tmp_file.parent / "different-location"
    tmp_file.unlink()

    assert not tmp_file.exists()

    step = migration_steps.Absent(str(tmp_file))
    assert step.validate()
    step.snapshot(tmp_path)
    step.run()
    step.rollback(tmp_path)


def test_absent_step_folder(tmp_folder):
    tmp_path = tmp_folder.parent / "different-location"

    assert (tmp_folder / "example-2.txt").exists()

    step = migration_steps.Absent(str(tmp_folder))
    assert step.validate()
    step.snapshot(tmp_path)
    step.run()

    assert not tmp_folder.exists()
    for i in range(3):
        fp = tmp_folder / f"example-{i}.txt"
        assert not fp.exists()

    step.rollback(tmp_path)

    assert tmp_folder.exists()
    for i in range(3):
        fp = tmp_folder / f"example-{i}.txt"
        assert fp.exists()


def test_move_step_file(tmp_file):
    tmp_path = tmp_file.parent / "different-location"
    new_path = tmp_file.parent / "new-location"
    new_path.mkdir()

    step = migration_steps.Move(str(tmp_file), str(new_path / tmp_file.name))
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
    tmp_path = tmp_folder.parent / "different-location"
    new_path = tmp_folder.parent / "new-location"

    step = migration_steps.Move(str(tmp_folder), str(new_path))
    assert step.validate()
    step.snapshot(tmp_path)
    step.run()

    assert not tmp_folder.exists()
    assert new_path.exists()

    step.rollback(tmp_path)

    assert tmp_folder.exists()
    assert not new_path.exists()


def test_symlink_step(tmp_file):
    tmp_path = tmp_file.parent / "different-location"
    new_path = tmp_file.parent / "new-location"
    new_path.mkdir()

    step = migration_steps.Symlink(str(tmp_file), str(new_path / tmp_file.name))
    assert step.validate()
    step.snapshot(tmp_path)
    step.run()

    new_file = new_path / tmp_file.name
    assert new_file.exists()
    assert new_file.is_symlink()

    step.rollback(tmp_path)
    assert not new_file.exists()
