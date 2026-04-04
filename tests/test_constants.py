import re
import os
from local_cli_agent import constants


def test_version_format():
    assert re.match(r'^\d+\.\d+\.\d+$', constants.VERSION)


def test_ansi_codes_start_with_escape():
    for color in [constants.RESET, constants.BOLD, constants.CYAN, constants.GREEN,
                  constants.YELLOW, constants.MAGENTA, constants.RED, constants.BLUE]:
        assert color.startswith("\033[")


def test_api_url_is_https():
    assert constants.API_URL.startswith("https://")


def test_memory_file_is_absolute():
    assert os.path.isabs(constants.MEMORY_FILE)


def test_changelog_is_absolute():
    assert os.path.isabs(constants.CHANGELOG)


def test_env_file_is_absolute():
    assert os.path.isabs(constants.ENV_FILE)


def test_script_dir_exists():
    assert os.path.isdir(constants.SCRIPT_DIR)


def test_script_dir_is_project_root():
    # local_cli_agent/ package should be inside SCRIPT_DIR
    assert os.path.isdir(os.path.join(constants.SCRIPT_DIR, "local_cli_agent"))
