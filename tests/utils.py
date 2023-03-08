import shutil
import sys
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

TEST_ROOT = Path(__file__).resolve().parent


def load_module(name, path):
    """Utility to load python files that aren't part of a regular package/module"""
    path = str(path)
    loader = SourceFileLoader(name, path)
    spec = spec_from_loader(name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    sys.modules[name] = module
    return module


def copy_migration(migration, target_dir, target="0.0.1"):
    migration = TEST_ROOT / "migrations" / f"{migration}.py"
    shutil.copy(migration, target_dir / f"{target}.py")
