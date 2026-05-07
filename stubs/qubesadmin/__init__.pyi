# Type stubs for the `qubesadmin` package, covering the surface area used by
# SecureDrop Workstation. Only includes what's covered by SDW code; full API at:
#
#   https://github.com/QubesOS/qubes-core-admin-client
#
# Layout mirrors the runtime package so import paths resolve identically at
# type-check and run time, e.g. `from qubesadmin.vm import QubesVM`.
from qubesadmin.app import VMCollection
from qubesadmin.vm import QubesVM

class Qubes:
    domains: VMCollection
    default_dispvm: QubesVM
    def __init__(self) -> None: ...
