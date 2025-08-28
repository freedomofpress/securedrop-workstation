---
name: Release
about: Create a release planning issue for SecureDrop Workstation
title: "Release SecureDrop Workstation [VERSION]"
labels: ["release"]
---

## Description
Release [SecureDrop Workstation [VERSION]](https://github.com/freedomofpress/securedrop-workstation/milestone/[MILESTONE_NUMBER])

**Release Roles:**
- RM:
- Deputy RM:
- Comms:

### Pre-release tasks
- [ ] Merge remaining PRs:
  - [ ] #[PR_NUMBER]

### Release tasks
- [ ] Assign roles
- [ ] RC version + changelog bump
- [ ] Publish packages on yum-test
- [ ] QA against yum-test
- [ ] Production version bump, changelog, and signed tag
- [ ] Production QA (yum-qa)
- [ ] Production release
- [ ] Forward `securedrop-workstation-docs` stable tag to publish docs updates
- [ ] Publish release commms

### Post-release tasks
- [ ] Run the updater on a production setup and perform smoke tests
- [ ] Backport version and changelog updates to `main`

## Test Plan

### Fresh install

### Upgrade testing

### Additional testing (if applicable)
