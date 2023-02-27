import sys
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader


def load_module(name, path):
    """Utility to load python files that aren't part of a regular package/module"""
    path = str(path)
    loader = SourceFileLoader(name, path)
    spec = spec_from_loader(name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    sys.modules[name] = module
    return module
