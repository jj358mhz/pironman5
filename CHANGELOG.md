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

## [fork-v0.1.1] - package 1.3.20

### Fixed
- `history_migrate.py`: `NameError`/`UnboundLocalError` crash in
  `run_migrate_history()` when InfluxDB reports a "partial write" on the
  `SELECT INTO` migration query (the exact scenario the tool exists for -
  migrated data spanning the retention-policy boundary). (#2)
- `_cli.py`: `update_config_file()` crashed with `JSONDecodeError` if
  `config.json` was empty or corrupt (e.g. from an interrupted write or a
  disk-full condition); it now falls back to an empty config and
  continues, matching the recovery `main()` already did for the in-memory
  read path. (#4)
- `docker-entrypoint.sh`: the `shutdown`/`systemctl`/`sudo` wrapper
  scripts matched target words as substrings of the whole command line,
  so e.g. `shutdown -c` (cancel) or `sudo journalctl -u
  shutdown-check.service` triggered a real forced host `poweroff -f`.
  Matching is now done per-argument/subcommand instead of across the
  whole command line. This also fixes a second bug in the `sudo`
  wrapper where `sudo systemctl reboot` incorrectly powered off instead
  of rebooting. (#8)

## [fork-v0.1.0] - package 1.3.19

### Added
- CI: a `lint-and-test` GitHub Actions workflow that runs the `tests/`
  suite with pytest on every pull request, satisfying the branch
  protection rule on `v1`.
- This CHANGELOG.
