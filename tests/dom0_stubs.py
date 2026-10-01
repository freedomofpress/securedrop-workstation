"""
Stand-ins for dom0-only modules (qubesadmin, dnf, systemd), so that the test
suite can be collected outside of dom0.

Importing from the stubs works, but actually using them raises `Dom0Required`.
Tests that need the real thing should use the `needs_dom0` fixture.
"""

import socket
import sys
import types
from typing import Any, NoReturn

IN_DOM0 = socket.gethostname() == "dom0"


class Dom0Required(RuntimeError):
    pass


def _fail(*args: Any, **kwargs: Any) -> NoReturn:
    raise Dom0Required(
        "This dom0-only module isn't available here; mock it or use the needs_dom0 fixture"
    )


class _Unavailable:
    # A real class, so it can still be used in annotations and as a base class
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _fail()


def _stub_modules(modules: dict[str, dict[str, Any]]) -> None:
    """Register stub modules, unless the real ones are all importable"""
    try:
        for name in modules:
            __import__(name)
        return
    except ImportError:
        pass

    for name, attrs in modules.items():
        module = types.ModuleType(name)
        module.__dict__.update(attrs, __dom0_stub__=True)
        sys.modules[name] = module
        parent, _, child = name.rpartition(".")
        if parent:
            setattr(sys.modules[parent], child, module)


def install() -> None:
    _stub_modules(
        {
            "qubesadmin": {"Qubes": _Unavailable},
            "qubesadmin.app": {"VMCollection": _Unavailable},
            "qubesadmin.vm": {"QubesVM": _Unavailable},
            "qubesadmin.exc": {"QubesException": type("QubesException", (Exception,), {})},
            "qubesadmin.tests": {},
            "qubesadmin.tests.mock_app": {
                "MockQube": _Unavailable,
                "QubesTestWrapper": _Unavailable,
            },
        }
    )
    _stub_modules(
        {
            "dnf": {},
            "dnf.rpm": {"detect_releasever": _fail},
        }
    )
    _stub_modules(
        {
            "systemd": {},
            "systemd.journal": {"Reader": _Unavailable},
        }
    )
