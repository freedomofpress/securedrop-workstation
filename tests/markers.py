"""
Shorthand marks for the `needs_*` fixtures in conftest.py

Use them to decorate a test or class, e.g. `@needs_journalist`, or apply them
to a whole module with `pytestmark = needs_journalist`.
"""

import pytest

from tests.dom0_stubs import IN_DOM0

needs_dom0 = pytest.mark.usefixtures("needs_dom0")
needs_journalist = pytest.mark.usefixtures("needs_journalist")
needs_admin = pytest.mark.usefixtures("needs_admin")

skip_in_dom0 = pytest.mark.skipif(IN_DOM0, reason="Test cannot be run in dom0")
