# Changelog

All notable changes to this fork of `pironman5` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

This file tracks changes specific to the `jj358mhz/pironman5` fork. The
`pironman5` Python package version (`pironman5/version.py`) continues to
follow upstream's `1.3.x` line so that `pip install --upgrade` ordering
stays correct. Fork-specific release points are marked with their own
`fork-vX.Y.Z` git tags (see Releases below), independent of the package
version number.

## [Unreleased]

### Added
- CI: a `lint-and-test` GitHub Actions workflow that runs the `tests/`
  suite with pytest on every pull request, satisfying the branch
  protection rule on `v1`.
- This CHANGELOG.

## Releases

- `fork-v0.1.0` — baseline tag marking the start of this fork's own
  changelog/release tracking, before the bug-fix/enhancement pass
  described above.
