import copy
import os
from typing import Iterator

import requests


def get_api_token(token_filename: str) -> str:
    token_not_found_msg = f'Requested token file: {token_filename} not found'
    if os.path.dirname(token_filename) and not os.path.isfile(token_filename):
        raise TokenFileNotFound(token_not_found_msg)

    # Make sure that we're starting in a subdir of the home directory
    if os.path.expanduser('~') not in os.path.abspath(os.curdir):
        raise TokenFileNotFound(token_not_found_msg)

    for dirname in walk_up_to_home_dir():
        filename = os.path.join(dirname, token_filename)
        if os.path.isfile(filename):
            with open(filename) as f:
                return f.read().strip()

    raise TokenFileNotFound(token_not_found_msg)


def walk_up_to_home_dir() -> Iterator[str]:
    current_dir = os.path.abspath(os.curdir)
    home_dir = os.path.expanduser('~')

    while current_dir != home_dir:
        yield current_dir
        current_dir = os.path.dirname(current_dir)

    yield home_dir


class TokenFileNotFound(Exception):
    pass

