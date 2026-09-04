import argparse
import os

import pytest

from scripts.test_codex_plugins import codex_version, prepare_codex


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable shim")
def test_codex_binary_preserves_dispatcher_symlink(tmp_path):
    dispatcher = tmp_path / "dispatcher"
    dispatcher.write_text('#!/bin/sh\nprintf "%s\\n" "${0##*/}"\n')
    dispatcher.chmod(0o755)
    codex = tmp_path / "codex"
    codex.symlink_to(dispatcher)

    command = prepare_codex(argparse.Namespace(codex_bin=codex))

    assert codex_version(command, tmp_path) == "codex"
