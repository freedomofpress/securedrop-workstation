---
name: Release
about: Create a release planning issue for SecureDrop Workstation
title: "Release SecureDrop Workstation [VERSION]"
labels: ["release"]
projects: ["projects/17"]
---

## Description
Release [SecureDrop Workstation [VERSION]](https://github.com/freedomofpress/securedrop-workstation/milestone/[MILESTONE_NUMBER])

Refer to the [SecureDrop Workstation RM docs](https://developers.securedrop.org/en/latest/workstation_release_management.html) for detailed instructions.

**Release Roles:**
- RM:
- Deputy RM:
- Comms:

### Pre-release tasks
- [ ] Merge remaining PRs:
  - [ ] #[PR_NUMBER]
- [ ] Update docs

### Release tasks
- [ ] Assign roles
- [ ] RC version + changelog bump
- [ ] Publish packages on yum-test
- [ ] QA against yum-test
- [ ] Prepare release commms
- [ ] Production version bump, changelog, and signed tag
- [ ] Production QA (yum-qa)
- [ ] Production release
- [ ] Forward `securedrop-workstation-docs` stable tag to publish docs updates
- [ ] Publish release commms

### Post-release tasks
- [ ] Run the updater on a production setup and perform smoke tests
- [ ] Backport changelog updates and bump to RC1 of next minor version in `main`

## Test Plan

### Common tests

### Scenario: Fresh install

- `config.json` environment:
- Other QA setup notes:

### Scenario: Upgrade testing

- `config.json` environment:
- Other QA setup notes:

### Additional testing (if applicable)
