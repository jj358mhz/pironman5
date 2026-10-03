"""Regression test: `pironman5 -cp <custom path> pipower5 ...` must forward
the custom config path to the pipower5 sub-CLI, not the hardcoded default."""
import json
import os
import subprocess
import sys
import types
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

if "pironman5.pironman5" not in sys.modules:
    _stub = types.ModuleType("pironman5.pironman5")
    _stub.Pironman5 = object
    sys.modules["pironman5.pironman5"] = _stub

from pironman5 import _cli


def test_custom_config_path_is_forwarded_to_pipower5(tmp_path):
    custom_path = str(tmp_path / "custom-config.json")

    fake_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok\n", stderr="")

    with patch.object(sys, "argv", ["pironman5", "-cp", custom_path, "pipower5", "status"]), \
         patch.object(_cli, "PERIPHERALS", ["pipower5"]), \
         patch("subprocess.run", return_value=fake_result) as mock_run:
        _cli.main()

    assert mock_run.called
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "pipower5"
    assert cmd[1] == "-cp"
    assert cmd[2] == custom_path, (
        "pipower5 passthrough used %r instead of the custom -cp path %r"
        % (cmd[2], custom_path)
    )
