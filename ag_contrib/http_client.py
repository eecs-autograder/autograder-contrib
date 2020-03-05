import copy
from urllib.parse import urljoin

import requests

from . import utils


class HTTPClient:
    """
    A convenience class that can be used to send authenticated requests
    to the API. Its HTTP methods use the requests library
    (https://requests.readthedocs.io/), and so they accept all keyword
    arguments accepted by the corresponding requests methods.

    Avoid constructing HTTPClient directly.
    Instead, use HTTPClient.make_default.
    """

    @staticmethod
    def make_default(token_filename='.agtoken', base_url='https://autograder.io/'):
        """
        Creates an HTTPClient instance with the API token found in token_filename.
        Token file discovery works as follows:
        - If token_filename is just a filename (no path information),
        the current directory and every upward directory until the home
        directory will be searched for a file with that name.
        - If token_filename is an absolute path or a relative path that
        contains at least one directory, that file will be opened and
        the token read to it.

        base_url will be prepended to all URLs passed to the client's
        request methods and defaults to https://autograder.io/.
        """
        return HTTPClient(utils.get_api_token(token_filename), base_url)

    def __init__(self, api_token, base_url):
        """
        Avoid constructing HTTPClient directly.
        Instead, use HTTPClient.make_default.
        """
        self.api_token = api_token
        self.base_url = base_url

    def get(self, url, *args, **kwargs):
        return self.do_request(requests.get, url, *args, **kwargs)

    def get_paginated(self, url, *args, **kwargs):
        page_url = url
        while page_url:
            response = self.get(page_url, *args, **kwargs)
            check_response_status(response)
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
        # print(urljoin(self.base_url, url))
        return method_func(
            urljoin(self.base_url, url), *args, headers=headers, **kwargs)


def check_response_status(response: requests.Response):
    if not response.ok:
        try:
            print(response.json())
        except ValueError:
            print(response.text)

        response.raise_for_status()
