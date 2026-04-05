import re
import os
from local_cli_agent import constants


def test_version_format():
    assert re.match(r'^\d+\.\d+\.\d+$', constants.VERSION)


def test_ansi_codes_start_with_escape():
    for color in [constants.RESET, constants.BOLD, constants.CYAN, constants.GREEN,
                  constants.YELLOW, constants.MAGENTA, constants.RED, constants.BLUE]:
        assert color.startswith("\033[")


def test_memory_file_is_absolute():
    assert os.path.isabs(constants.MEMORY_FILE)


def test_changelog_is_absolute():
    assert os.path.isabs(constants.CHANGELOG)


def test_env_file_is_absolute():
    assert os.path.isabs(constants.ENV_FILE)


def test_script_dir_exists():
    assert os.path.isdir(constants.SCRIPT_DIR)


import pytest
import site as _site

def _is_editable_install():
    pkg_dir = os.path.dirname(os.path.abspath(constants.__file__))
    try:
        sp_dirs = _site.getsitepackages()
    except AttributeError:
        sp_dirs = []
    return not any(pkg_dir.startswith(sp) for sp in sp_dirs)


@pytest.mark.skipif(not _is_editable_install(), reason="Only valid for editable (dev) install")
def test_script_dir_is_project_root():
    # local_cli_agent/ package should be inside SCRIPT_DIR for editable installs
    assert os.path.isdir(os.path.join(constants.SCRIPT_DIR, "local_cli_agent"))
