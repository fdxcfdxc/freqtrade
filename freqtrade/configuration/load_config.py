"""
This module contain functions to load the configuration file
"""
import logging
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

import rapidjson

from freqtrade.constants import MINIMAL_CONFIG
from freqtrade.exceptions import OperationalException
from freqtrade.misc import deep_merge_dicts


logger = logging.getLogger(__name__)


CONFIG_PARSE_MODE = rapidjson.PM_COMMENTS | rapidjson.PM_TRAILING_COMMAS


def log_config_error_range(path: str, errmsg: str) -> str:
    """
    Parses configuration file and prints range around error
    """
    if path != '-':
        offsetlist = re.findall(r'(?<=Parse\serror\sat\soffset\s)\d+', errmsg)
        if offsetlist:
            offset = int(offsetlist[0])
            text = Path(path).read_text()
            # Fetch an offset of 80 characters around the error line
            subtext = text[offset-min(80, offset):offset+80]
            segments = subtext.split('\n')
            if len(segments) > 3:
                # Remove first and last lines, to avoid odd truncations
                return '\n'.join(segments[1:-1])
            else:
                return subtext
    return ''


def load_file(path: Path) -> Dict[str, Any]:
    try:
        with path.open('r') as file:
            config = rapidjson.load(file, parse_mode=CONFIG_PARSE_MODE)
    except FileNotFoundError:
        raise OperationalException(f'File "{path}" not found!')
    return config


def load_config_file(path: str) -> Dict[str, Any]:
    """
    Loads a config file from the given path
    :param path: path as str
    :return: configuration as dictionary
    """
    try:
        # Read config from stdin if requested in the options
        with open(path) if path != '-' else sys.stdin as file:
            config = rapidjson.load(file, parse_mode=CONFIG_PARSE_MODE)
    except FileNotFoundError:
        raise OperationalException(
            f'Config file "{path}" not found!'
            ' Please create a config file or check whether it exists.')
    except rapidjson.JSONDecodeError as e:
        err_range = log_config_error_range(path, str(e))
        raise OperationalException(
            f'{e}\n'
            f'Please verify the following segment of your configuration:\n{err_range}'
            if err_range else 'Please verify your configuration file for syntax errors.'
        )

    return config


def load_from_files(files: List[str]) -> Dict[str, Any]:

    config: Dict[str, Any] = {}

    if not files:
        return deepcopy(MINIMAL_CONFIG)

    # We expect here a list of config filenames
    for path in files:
        logger.info(f'Using config: {path} ...')
        # Merge config options, overwriting old values
        config = deep_merge_dicts(load_config_file(path), config)

    config['config_files'] = files

    return config
