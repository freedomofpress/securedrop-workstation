# SDW python stubs

Directory for [mypy stubs](https://mypy.readthedocs.io/en/stable/stubs.html) for SecureDrop Workstation.
Mostly we stub the `qubesadmin` import types, so that our code can retain strong types,
maximizing linter utility.

We don't need to copy the upstream function signatures wholesale; we only need to provide
annotations for the functions that the SDW code actually uses.

## Resources

Consult the upstream repo for [qubes-core-admin-client](https://github.com/QubesOS/qubes-core-admin-client)
for details on the `qubesadmin` types.
