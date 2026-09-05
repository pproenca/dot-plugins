"""Keep the installed plugin's standalone behavioral suite in repository CI."""

import subprocess
import sys

from conftest import PLUGINS_DIR


def test_domain_mapping_behavioral_suite():
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=PLUGINS_DIR / "domain-mapping",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
