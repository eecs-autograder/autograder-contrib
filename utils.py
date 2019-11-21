import copy
import os
from typing import Iterator
from urllib.parse import urljoin

import requests

import utils


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


def check_response_status(response: requests.Response):
    if not response.ok:
        try:
            print(response.json())
        except ValueError:
            print(response.text)

        response.raise_for_status()


class HTTPClient:
    def __init__(self, api_token, base_url):
        self.api_token = api_token
        self.base_url = base_url

    def get(self, url, *args, **kwargs):
        return self.do_request(requests.get, url, *args, **kwargs)

    def get_paginated(self, url, *args, **kwargs):
        page_url = url
        while page_url:
            response = self.get(page_url, *args, **kwargs)
            utils.check_response_status(response)
            for item in response.json()['results']:
                yield item

            page_url = response.json()['next']

    def post(self, url, *args, **kwargs):
        return self.do_request(requests.post, url, *args, **kwargs)

    def put(self, url, *args, **kwargs):
        return self.do_request(requests.put, url, *args, **kwargs)

    def patch(self, url, *args, **kwargs):
        return self.do_request(requests.patch, url, *args, **kwargs)

    def delete(self, url, *args, **kwargs):
        return self.do_request(requests.delete, url, *args, **kwargs)

    def do_request(self, method_func, url, *args, **kwargs):
        headers = copy.deepcopy(kwargs.pop('headers', {}))
        headers['Authorization'] = f'Token {self.api_token}'
        return method_func(
            urljoin(self.base_url, url), *args, headers=headers, **kwargs)
