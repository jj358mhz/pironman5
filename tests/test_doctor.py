"""Tests for pironman5.doctor — InfluxDB upgrade repair helpers."""
import json
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pironman5.doctor import find_duplicate_keys, _comment_out_duplicates, run_doctor


# A config file mangled by upgrading from 1.2.x: the legacy dashboard
# appended log-enabled / level at the end of the section and earlier
# installers un-commented the original lines, so [http] and [logging] now
# define the same key twice and influxd refuses to start.
CORRUPTED_CONFIG = """\
[http]
# Determines whether HTTP request logging is enabled.
log-enabled = false

###
### [logging]
###

log-enabled = false
[logging]
# Determines which level of logs will be emitted.
level = "error"

###
### [subscriber]
###

level = "error"
[subscriber]
# enabled = true
"""


def _write(tmp_path, text):
    path = os.path.join(str(tmp_path), "influxdb.conf")
    with open(path, "w") as handle:
        handle.write(text)
    return path


def _active_lines(content):
    return [
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def test_find_duplicate_keys_reports_each_duplicate(tmp_path):
    path = _write(tmp_path, CORRUPTED_CONFIG)
    duplicates = find_duplicate_keys(path)
    assert [(section, key) for _, section, key in duplicates] == [
        ("[http]", "log-enabled"),
        ("[logging]", "level"),
    ]


def test_fix_removes_duplicates_and_keeps_first_value(tmp_path):
    path = _write(tmp_path, CORRUPTED_CONFIG)
    assert _comment_out_duplicates(path) == 2
    assert find_duplicate_keys(path) == []

    with open(path) as handle:
        content = handle.read()
    active = _active_lines(content)
    assert active.count("log-enabled = false") == 1
    assert active.count('level = "error"') == 1
    # the removed duplicates are kept around as comments for traceability
    assert content.count("# pironman5 doctor: duplicate key removed -> ") == 2


def test_fix_is_idempotent(tmp_path):
    path = _write(tmp_path, CORRUPTED_CONFIG)
    _comment_out_duplicates(path)
    assert _comment_out_duplicates(path) == 0


def test_clean_config_has_no_duplicates(tmp_path):
    path = _write(
        tmp_path,
        "[http]\n# log-enabled = true\nlog-enabled = false\n\n[logging]\nlevel = \"error\"\n",
    )
    assert find_duplicate_keys(path) == []
    assert _comment_out_duplicates(path) == 0


def test_missing_file_is_not_an_error(tmp_path):
    assert find_duplicate_keys(os.path.join(str(tmp_path), "nope.conf")) == []


def _fake_run(cmd):
    """Stand in for pironman5.doctor._run - no real subprocess calls.

    Reports influxd as installed, and the influxd.service already active
    and enabled, so run_doctor's fix path only has to create the (missing
    in this sandbox) /var/lib/influxdb data directory - everything else
    (config file, pironman5.service, work/log dirs) legitimately doesn't
    exist here, so those checks naturally skip themselves without any
    further mocking.
    """
    if cmd.startswith("command -v influxd"):
        return 0, "/usr/bin/influxd"
    if cmd.startswith("systemctl is-active"):
        return 0, "active"
    if cmd.startswith("systemctl is-enabled"):
        return 0, "enabled"
    if cmd.startswith("mkdir -p"):
        return 0, ""
    return 0, ""


def _run_doctor_fix_json(reachable_then):
    """Run `pironman5 doctor --fix --json` with _run/_influxdb_reachable
    mocked out, and return the parsed JSON result list."""
    with patch("pironman5.doctor._run", side_effect=_fake_run), \
         patch("pironman5.doctor._influxdb_reachable", side_effect=reachable_then), \
         patch("builtins.print") as mock_print:
        run_doctor(fix=True, as_json=True)
    printed = "\n".join(str(call.args[0]) for call in mock_print.call_args_list if call.args)
    return json.loads(printed)["results"]


def test_doctor_fix_reports_detail_as_string_when_reachable():
    """Regression test for the trailing-comma bug: result.detail for the
    influxdb HTTP API check must be a str, not a 1-element tuple, when the
    re-verify pass finds InfluxDB reachable."""
    results = _run_doctor_fix_json(reachable_then=[False, True])
    api_result = next(r for r in results if r["name"].startswith("influxdb HTTP API"))
    assert api_result["detail"] == "PONG"
    assert isinstance(api_result["detail"], str)


def test_doctor_fix_reports_detail_as_string_when_unreachable():
    """Same regression test, for the 'still unreachable' branch of the
    same ternary."""
    results = _run_doctor_fix_json(reachable_then=[False, False])
    api_result = next(r for r in results if r["name"].startswith("influxdb HTTP API"))
    assert api_result["detail"] == "no response - check journalctl -u influxdb"
    assert isinstance(api_result["detail"], str)
