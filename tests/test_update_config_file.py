"""Tests for update_config_file — patches config.json in place from the CLI."""
import json
import os
import sys
import tempfile
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# pironman5._cli imports pironman5.pironman5 (for the Pironman5 app
# class), which imports pm_auto/sf_rpi_status (installed by the hardware
# installer, not available on PyPI) and opens /var/log/pironman5/ as a
# module-level side effect. update_config_file doesn't touch any of
# that, so stub the whole pironman5.pironman5 module out rather than
# letting it actually run.
if "pironman5.pironman5" not in sys.modules:
    _stub = types.ModuleType("pironman5.pironman5")
    _stub.Pironman5 = object
    sys.modules["pironman5.pironman5"] = _stub

from pironman5._cli import update_config_file


def _with_temp_config(content):
    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    return path


def test_empty_file_does_not_crash():
    """Scenario: config.json is 0 bytes (interrupted write, disk full, etc.)."""
    path = tempfile.mkstemp()[1]
    try:
        update_config_file({'system': {'temperature_unit': 'F'}}, path)
        with open(path) as f:
            result = json.load(f)
        assert result == {'system': {'temperature_unit': 'F'}}
        print("  Empty config.json: no crash, OK")
    finally:
        os.remove(path)


def test_corrupt_file_does_not_crash():
    """Scenario: config.json has partial/invalid JSON."""
    path = _with_temp_config('{"system": {')
    try:
        update_config_file({'system': {'temperature_unit': 'F'}}, path)
        with open(path) as f:
            result = json.load(f)
        assert result == {'system': {'temperature_unit': 'F'}}
        print("  Corrupt config.json: no crash, OK")
    finally:
        os.remove(path)


def test_existing_config_is_merged():
    """Normal case: existing keys are preserved, patched keys are updated."""
    path = _with_temp_config(json.dumps({'system': {'temperature_unit': 'C', 'data_interval': 5}}))
    try:
        update_config_file({'system': {'temperature_unit': 'F'}}, path)
        with open(path) as f:
            result = json.load(f)
        assert result == {'system': {'temperature_unit': 'F', 'data_interval': 5}}
        print("  Existing config merge: OK")
    finally:
        os.remove(path)


if __name__ == "__main__":
    test_empty_file_does_not_crash()
    test_corrupt_file_does_not_crash()
    test_existing_config_is_merged()
    print("\nAll update_config_file tests passed.")
