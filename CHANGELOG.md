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

## [fork-v0.1.7] - package 1.3.26

Closes the remainder of #9.

### Fixed
- `install.sh`: the DKMS-install failure fallback unconditionally wrote
  a Debian "trixie" apt source on *any* `apt-get install -y dkms`
  failure, with no OS check. On a non-Debian-family system (e.g.
  Ubuntu) this risked a mixed-release ("Frankendebian") apt
  configuration. Now only applies on Debian/Raspberry Pi OS
  (`ID=debian` or `ID=raspbian` in `/etc/os-release`); everywhere else
  it fails with a clear message instead of guessing. Fixed at both of
  the file's two (duplicated) occurrences.
- `scripts/setup_pipower5.sh`: `useradd -g pipower5` had no preceding
  `groupadd`, so it would fail with "group 'pipower5' does not exist"
  on a fresh system. Added `groupadd -r pipower5` first, matching
  `install.sh`'s own current pattern. This script is currently orphaned
  (not referenced by `install.sh`), so there's no live impact today,
  but it's fixed in case it's ever invoked directly or resurrected.
- `scripts/install_influxdb.sh`: wrote the InfluxDB GPG key to
  `/etc/apt/keyrings/influxdata-archive.gpg` without ensuring that
  directory exists first, failing on a system where it hasn't already
  been created by something else. Added `mkdir -p /etc/apt/keyrings`.

### Changed
- `bin/pironman5.service`: added a comment documenting *why* this unit
  must keep running as `User=root`/`Group=root` rather than the
  unprivileged `pironman5` user `install.sh` sets up. Verified against
  `sf_rpi_status`'s actual source: `shutdown()`/`reboot()` use `sudo
  systemctl poweroff/reboot -i` (would work fine unprivileged, since the
  sudoers rule grants NOPASSWD for `/usr/bin/systemctl`), but
  `restart_service()` runs a bare `systemctl restart <service>` with no
  `sudo` prefix at all - switching `User=` would silently break
  pm_dashboard's "restart service" button until that upstream call is
  fixed to use `sudo` too. No code change here; this documents a
  verified constraint so it isn't "fixed" into a regression later.

## [fork-v0.1.6] - package 1.3.25

### Added
- `install.sh`: new `--pironman5-repo <url>` flag (and matching
  `PIRONMAN5_REPO` environment variable), parallel to the existing
  `--pironman5-branch`/`PIRONMAN5_BRANCH`. Overrides where the
  `pironman5` repo itself is cloned from, so you can install from a
  personal fork without needing forks of `pm_auto`, `pm_dashboard`,
  `sf_rpi_status` or `pipower5` too - those still come from sunfounder's
  `GIT_REPO` as before. Also derives the matching raw-content base URL
  so the installer's version report reflects the fork, not upstream.

  ```bash
  curl -sSL https://raw.githubusercontent.com/jj358mhz/pironman5/v1/install.sh | \
    sudo bash -s -- --variant promax --pironman5-repo https://github.com/jj358mhz/pironman5.git
  ```

## [fork-v0.1.5] - package 1.3.24

### Added
- `doctor.py`: new check that `/opt/pironman5/config.json` exists and is
  valid JSON. `--fix` resets an empty/corrupt file to `{"system": {}}`;
  without `--fix` it's reported as a failure explaining that the service
  won't start correctly. Closes #10.
- Test coverage for `run_doctor()`'s orchestration logic: the new
  config.json check (missing/empty/corrupt/valid, with and without
  `--fix`), plus a broad regression guard asserting every `Result.detail`
  in any `run_doctor()` output - fix or no-fix - is a string. Closes #11.

## [fork-v0.1.4] - package 1.3.23

### Fixed
- `install.sh`: "Pironman 5 NAS" was advertised in the banner and fully
  defined in `pironman5/variants/products.py` (with its own `.dtbo` and
  a dedicated RTL8125 2.5G NIC setup script), but the installer's
  `--variant` validator, interactive menu, and overlay map had no `nas`
  entry at all, making the product completely unreachable through the
  shipped installer. Added `nas` to all three, and wired
  `scripts/setup_rtl8125.sh` into the post-install step for that variant
  (builds the `rtnicpg` driver and programs the NIC's EFUSE MAC address
  if it isn't set yet). (#6)

### Changed
- `CLAUDE.md`: added the `nas` row to the variants/modules table.

## [fork-v0.1.3] - package 1.3.22

### Fixed
- `utils.py`: `merge_dict()` wrote through its `dict1` argument
  (`dict1[key] = {}`) instead of only building `new_dict`, which could
  permanently corrupt the shared `SYSTEM_DEFAULT_CONFIG` module-level
  singleton for the rest of the process when a config override supplied
  a malformed nested-dict value. `build_effective_config()` relies on
  `merge_dict` being read-only, and `pipower5_buzz_sequence` is the one
  default config value shaped as a nested dict in production. `dict1` is
  now never mutated, and a type mismatch (e.g. a dict override where the
  default is a scalar) falls back to an empty base instead of crashing.
  (#9, partial)

### Added
- Regression test `tests/test_cli_show_config.py::test_merge_dict_readonly_nested`,
  closing the coverage gap identified in #12 (the existing
  `test_readonly_defaults` only exercises a flat-key override and could
  never have caught this).

## [fork-v0.1.2] - package 1.3.21

### Fixed
- `doctor.py`: a stray trailing comma turned `result.detail` into a
  1-element tuple instead of a string for the "influxdb HTTP API"
  re-verify check after `doctor --fix`, corrupting both the text and
  JSON output. (#1)
- `_cli.py`: `pironman5 plugin` with no sub-subcommand crashed with
  `AttributeError` instead of showing a usage error; the `plugin_action`
  subparser is now marked `required=True`. (#3)
- `_cli.py`: `pironman5 -cp <path> pipower5 ...` ignored the custom
  config path and forwarded the hardcoded default to the `pipower5`
  sub-CLI instead - fixed a variable-name typo (`CONFIG_PATH` vs.
  `config_path`). (#5)
- `install.sh`: `--plugin` read and then immediately discarded its
  argument, and the stray extra `shift` could swallow the *next*
  command-line flag entirely (e.g. `--plugin --container` silently
  dropped `--container`). It's now a plain no-argument flag, matching
  `--pipower5`. (#7)

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
