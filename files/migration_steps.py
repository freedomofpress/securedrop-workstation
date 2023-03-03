"""
General purpose migration steps and utilities
"""

import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class MigrationStep(ABC):  # pragma: no cover
    """
    Abstract base class to specify the API for migration steps
    """

    def validate(self) -> bool:
        return True

    def tmpdir(self, parent: Path, suffix: int) -> Path:
        return parent / f"{self.__class__.__name__}{suffix}"

    def snapshot(self, tmpdir: Path) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass

    def rollback(self, tmpdir: Path) -> None:
        pass

    def cleanup(self, tmpdir) -> None:
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.__dict__}>"

    def __str__(self) -> str:
        return self.__repr__()


def path_remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def path_validate(path: Path, check_exists: Optional[bool]) -> bool:
    # None: no check
    # True: check if it exists
    # False: check if it doesn't exist
    if check_exists is not None:
        return path.exists() == check_exists
    return True


def path_snapshot(path: Path, tmpdir: Path) -> None:
    if path.is_dir():
        shutil.copytree(path, tmpdir / path.name)
    else:
        shutil.copy2(path, tmpdir)


def path_rollback(path: Path, tmpdir: Path) -> None:
    shutil.move(f"{tmpdir}/{path.name}", path)


class Absent(MigrationStep):
    """
    Check for the absence of, or remove a path (file or folder)

    - If check_exists is None (default), the supplied path will be removed if it exists, but no
      validation error will be raised if it does not exist
    - If check_exists is True, the supplied path will be removed, but a validation error will be
      raised if the path does not exist in the first place
    - If check_exists is False, the supplied path will be confirmed to not exist, a validation error
      will be raised if it does exist

    Folders are removed recursively along with their contents.
    """

    def __init__(self, path: Path, check_exists: Optional[bool] = None) -> None:
        self.path = Path(path)
        self.check_exists = check_exists
        self.rolled_back = False

    def validate(self) -> bool:
        return path_validate(self.path, self.check_exists)

    def snapshot(self, tmpdir: Path) -> None:
        if self.path.exists():
            path_snapshot(self.path, tmpdir)
            self.rolled_back = True

    def run(self) -> None:
        if self.path.exists():
            path_remove(self.path)

    def rollback(self, tmpdir: Path) -> None:
        if self.rolled_back:
            path_rollback(self.path, tmpdir)


class Move(MigrationStep):
    """Move a path (file or folder) to a target"""

    def __init__(self, path: Path, target: Path, check_exists: Optional[bool] = True):
        self.path = Path(path)
        self.target = Path(target)
        self.check_exists = check_exists

    def validate(self) -> bool:
        return path_validate(self.path, self.check_exists)

    def snapshot(self, tmpdir) -> None:
        path_snapshot(self.path, tmpdir)

    def run(self) -> None:
        self.path.rename(self.target)

    def rollback(self, tmpdir: Path) -> None:
        if self.target.exists():
            path_remove(self.target)
        path_rollback(self.path, tmpdir)


class Symlink(MigrationStep):
    """Create a symlink target to path (file or folder)"""

    def __init__(self, path: Path, target: Path, check_exists: Optional[bool] = True):
        self.path = Path(path)
        self.target = Path(target)
        self.check_exists = check_exists
        self.target_existed = False

    def validate(self) -> bool:
        return path_validate(self.path, self.check_exists)

    def run(self) -> None:
        self.target.symlink_to(self.path)

    def rollback(self, tmpdir: Path) -> None:
        self.target.unlink()
