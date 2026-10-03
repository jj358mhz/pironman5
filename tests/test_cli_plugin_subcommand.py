"""Regression test: `pironman5 plugin` with no sub-subcommand must show a
usage error, not crash with AttributeError."""
import os
import sys
import types
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

if "pironman5.pironman5" not in sys.modules:
    _stub = types.ModuleType("pironman5.pironman5")
    _stub.Pironman5 = object
    sys.modules["pironman5.pironman5"] = _stub

from pironman5 import _cli


def test_bare_plugin_subcommand_exits_cleanly(tmp_path, capsys):
    config_path = str(tmp_path / "config.json")

    with patch.object(sys, "argv", ["pironman5", "-cp", config_path, "plugin"]), \
         patch.object(_cli, "PERIPHERALS", []):
        try:
            _cli.main()
        except SystemExit as exc:
            # argparse's own "required" error exits with code 2 - this is
            # the expected, clean failure mode.
            assert exc.code == 2
        else:
            raise AssertionError("expected a clean SystemExit, got none")

    err = capsys.readouterr().err
    assert "plugin_action" in err
