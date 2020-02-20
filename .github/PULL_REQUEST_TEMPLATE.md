## Status

Ready for review / Work in progress

## Description of Changes

Fixes #.

Changes proposed in this pull request:

## Testing

How should the reviewer test this PR?
Write out any special testing steps here.

## Checklist

### If you have made code changes

- [ ] Linter (`make flake8`) passes in the development environment (this box may
      be left unchecked, as `flake8` also runs in CI)

### If you have made changes to the provisioning logic

- [ ] All tests (`make test`) pass in `dom0` of a Qubes install

- [ ] This PR adds/removes files, and includes required updates to the packaging
      logic in `MANIFEST.in` and `rpm-build/SPECS/securedrop-workstation-dom0-config.spec`
