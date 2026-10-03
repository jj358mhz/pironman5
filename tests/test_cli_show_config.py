"""Tests for build_effective_config — shared config assembly used by app & CLI."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pironman5.utils import build_effective_config, merge_dict


def test_empty_file():
    """Scenario 1: empty system → full defaults, no crash."""
    result = build_effective_config({'system': {}})
    assert 'system' in result
    assert len(result['system']) >= 17, \
        f"Expected >=17 keys, got {len(result['system'])}"
    from pironman5._constants import DEFAULT_DEBUG_LEVEL
    assert result['system']['debug_level'] == DEFAULT_DEBUG_LEVEL
    print(f"  Empty file: {len(result['system'])} config keys, OK")


def test_empty_system():
    """Scenario 2: {'system': {}} → full defaults."""
    result = build_effective_config({'system': {}})
    assert 'system' in result
    assert len(result['system']) >= 17, \
        f"Expected >=17 keys, got {len(result['system'])}"
    assert 'data_interval' in result['system']
    print(f"  Empty system: {len(result['system'])} config keys, OK")


def test_partial_override():
    """Scenario 3: only temperature_unit changed → defaults + override."""
    result = build_effective_config({'system': {'temperature_unit': 'F'}})
    assert 'system' in result
    assert len(result['system']) >= 17, \
        f"Expected >=17 keys, got {len(result['system'])}"
    assert result['system']['temperature_unit'] == 'F', \
        f"Expected 'F', got {result['system']['temperature_unit']}"
    assert 'data_interval' in result['system']
    assert 'database_retention_days' in result['system']
    print(f"  Partial override: {len(result['system'])} config keys, temp_unit=F, OK")


def test_legacy_auto():
    """Scenario 4: legacy {'auto': {...}} → migrated to system."""
    result = build_effective_config({'auto': {'temperature_unit': 'F'}})
    assert 'system' in result
    assert 'auto' not in result
    assert len(result['system']) >= 17, \
        f"Expected >=17 keys, got {len(result['system'])}"
    assert result['system']['temperature_unit'] == 'F'
    print(f"  Legacy auto: migrated to system, temp_unit=F, OK")


def test_no_file():
    """Scenario 5: raw_config=None → defaults only."""
    result = build_effective_config(None)
    assert 'system' in result
    assert len(result['system']) >= 17
    from pironman5._constants import DEFAULT_DEBUG_LEVEL
    assert result['system']['debug_level'] == DEFAULT_DEBUG_LEVEL
    print(f"  No file (None): {len(result['system'])} config keys, OK")


def test_readonly_input():
    """build_effective_config must not mutate its input."""
    original = {'system': {'temperature_unit': 'F'}}
    copy_before = json.dumps(original)
    build_effective_config(original)
    assert json.dumps(original) == copy_before, "Input was mutated!"
    print("  Read-only (no input mutation): OK")


def test_readonly_defaults():
    """build_effective_config must not mutate SYSTEM_DEFAULT_CONFIG."""
    from pironman5.variants import SYSTEM_DEFAULT_CONFIG
    copy_before = json.dumps(SYSTEM_DEFAULT_CONFIG)
    build_effective_config({'system': {'temperature_unit': 'F'}})
    assert json.dumps(SYSTEM_DEFAULT_CONFIG) == copy_before, \
        "SYSTEM_DEFAULT_CONFIG was mutated!"
    print("  Read-only (defaults not polluted): OK")


def test_merge_dict_readonly_nested():
    """merge_dict must not mutate dict1 for a nested-dict-shaped override.

    test_readonly_defaults above only overrides a flat scalar key, which
    can never hit the mutation path: it only triggers when the override
    supplies a dict value for a key that isn't already present one level
    inside an *existing* nested dict (the shape pipower5_buzz_sequence
    has in pironman5/variants/modules/pipower5.py). Regression test for
    the shared-singleton corruption this caused (see issue #9).
    """
    shared_nested = {'battery_activated': [['A4', 200]]}
    dict1 = {'pipower5_buzz_sequence': shared_nested}
    before = json.dumps(dict1)

    dict2 = {'pipower5_buzz_sequence': {'some_new_event': {'bad': 'shape'}}}
    merge_dict(dict1, dict2)

    assert json.dumps(dict1) == before, "merge_dict mutated dict1!"
    assert 'some_new_event' not in shared_nested, \
        "merge_dict mutated the shared nested dict in place!"
    print("  merge_dict read-only (nested dict not polluted): OK")


if __name__ == "__main__":
    test_empty_file()
    test_empty_system()
    test_partial_override()
    test_legacy_auto()
    test_no_file()
    test_readonly_input()
    test_readonly_defaults()
    test_merge_dict_readonly_nested()
    print("\nAll build_effective_config tests passed.")
