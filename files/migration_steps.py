"""
General purpose migration steps and utilities
"""

import shutil
from abc import ABC, abstractmethod
from pathlib import Path


class MigrationStep(ABC):
    """
    Abstract base class to specify the API for migration steps
    """

    def validate(self):
        return True

    def snapshot(self, tmpdir):
        pass

    @abstractmethod
    def run(self):  # pragma: no cover
        pass

    def rollback(self, tmpdir):
        pass

    def cleanup(self, tmpdir):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.__dict__}>"

    def __str__(self):
        return self.__repr__()


def path_remove(path):
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def path_validate(path, check_exists):
    # None: no check
    # True: check if it exists
    # False: check if it doesn't exist
    if check_exists is not None:
        return path.exists() == check_exists
    return True


def path_snapshot(path, tmpdir):
    if path.is_dir():
        shutil.copytree(path, tmpdir / path.name)
    else:
        shutil.copy2(path, tmpdir)


def path_rollback(path, tmpdir):
    shutil.move(f"{tmpdir}/{path.name}", path)


class Absent(MigrationStep):
    def __init__(self, path, check_exists=None):
        self.path = Path(path)
        self.check_exists = check_exists
        self.rolled_back = False

    def validate(self):
        return path_validate(self.path, self.check_exists)

    def snapshot(self, tmpdir):
        if self.path.exists():
            path_snapshot(self.path, tmpdir)
            self.rolled_back = True

    def run(self):
        if self.path.exists():
            path_remove(self.path)

    def rollback(self, tmpdir):
        if self.rolled_back:
            path_rollback(self.path, tmpdir)


class Move(MigrationStep):
    def __init__(self, path, target, check_exists=True):
        self.path = Path(path)
        self.target = Path(target)
        self.check_exists = check_exists

    def validate(self):
        return path_validate(self.path, self.check_exists)

    def snapshot(self, tmpdir):
        path_snapshot(self.path, tmpdir)

    def run(self):
        self.path.rename(self.target)

    def rollback(self, tmpdir):
        if self.target.exists():
            path_remove(self.target)
        path_rollback(self.path, tmpdir)


class Symlink(MigrationStep):
    def __init__(self, path, target, check_exists=True):
        self.path = Path(path)
        self.target = Path(target)
        self.check_exists = check_exists
        self.target_existed = False

    def validate(self):
        return path_validate(self.path, self.check_exists)

    def run(self):
        self.target.symlink_to(self.path)

    def rollback(self, tmpdir):
        self.target.unlink()
