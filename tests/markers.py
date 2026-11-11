"""
Shorthand marks for the `needs_*` fixtures in conftest.py

Use them to decorate a test or class, e.g. `@needs_journalist`, or apply them
to a whole module with `pytestmark = needs_journalist`.
"""

import socket

import pytest

IN_DOM0 = socket.gethostname() == "dom0"

needs_dom0 = pytest.mark.usefixtures("needs_dom0")
needs_journalist = pytest.mark.usefixtures("needs_journalist")
needs_admin = pytest.mark.usefixtures("needs_admin")
