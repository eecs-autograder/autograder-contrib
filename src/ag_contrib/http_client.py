import argparse
import json
from typing import TYPE_CHECKING, Mapping, TypeAlias, TypedDict
from urllib.parse import urljoin

import requests
from requests.models import HTTPError
from typing_extensions import Unpack

from . import utils

_HeadersMapping: TypeAlias = Mapping[str, str | bytes]
if TYPE_CHECKING:
    from _typeshed import Incomplete
    from requests.sessions import (
        RequestsCookieJar,
        _Auth,  # pyright: ignore[reportPrivateUsage]
        _Cert,  # pyright: ignore[reportPrivateUsage]
        _Data,  # pyright: ignore[reportPrivateUsage]
        _Files,  # pyright: ignore[reportPrivateUsage]
        _HooksInput,  # pyright: ignore[reportPrivateUsage]
        _Params,  # pyright: ignore[reportPrivateUsage]
        _TextMapping,  # pyright: ignore[reportPrivateUsage]
        _Timeout,  # pyright: ignore[reportPrivateUsage]
        _Verify,  # pyright: ignore[reportPrivateUsage]
    )

    class RequestKwargs(TypedDict, total=False):
        params: _Params | None
        data: _Data | None
        headers: _HeadersMapping | None
        cookies: RequestsCookieJar | _TextMapping | None
        files: _Files | None
        auth: _Auth | None
        timeout: _Timeout | None
        allow_redirects: bool
        proxies: _TextMapping | None
        hooks: _HooksInput | None
        stream: bool | None
        verify: _Verify | None
        cert: _Cert | None
        json: Incomplete | None

else:

    class RequestKwargs(TypedDict):
        pass


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
    def make_default(token_filename: str = ".agtoken", base_url: str = "https://autograder.io/"):
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

    def __init__(self, api_token: str, base_url: str):
        """
        Avoid constructing HTTPClient directly.
        Instead, use HTTPClient.make_default.
        """
        self.api_token = api_token
        self.base_url = base_url

    def get(self, url: str, **kwargs: Unpack[RequestKwargs]):
        return self.do_request("get", url, **kwargs)

    def get_paginated(self, url: str, **kwargs: Unpack[RequestKwargs]):
        page_url = url
        while page_url:
            response = self.get(page_url, **kwargs)
            check_response_status(response)
            for item in response.json()["results"]:
                yield item

            page_url = response.json()["next"]

    def post(self, url: str, **kwargs: Unpack[RequestKwargs]):
        return self.do_request("post", url, **kwargs)

    def put(self, url: str, **kwargs: Unpack[RequestKwargs]):
        return self.do_request("put", url, **kwargs)

    def patch(self, url: str, **kwargs: Unpack[RequestKwargs]):
        return self.do_request("patch", url, **kwargs)

    def delete(self, url: str, **kwargs: Unpack[RequestKwargs]):
        return self.do_request("delete", url, **kwargs)

    def do_request(self, method: str, url: str, **kwargs: Unpack[RequestKwargs]):
        updated_headers = {}
        if "headers" in kwargs and kwargs["headers"] is not None:
            updated_headers = dict(kwargs["headers"])

        updated_headers["Authorization"] = f"Token {self.api_token}"
        kwargs["headers"] = updated_headers

        return requests.request(method, urljoin(self.base_url, url), **kwargs)


def check_response_status(response: requests.Response):
    if not response.ok:
        try:
            print(response.json())
        except ValueError:
            print(response.text)

        response.raise_for_status()


def main():
    args = parse_args()
    body: dict[str, object] = {} if args.json_body is None else json.loads(args.json_body)

    client = HTTPClient.make_default(token_filename=args.token_file, base_url=args.base_url)
    try:
        if args.action == "get":
            response = client.get(args.url)
            check_response_status(response)
            print(json.dumps(response.json(), indent=4))
        elif args.action == "get_pages":
            response = list(client.get_paginated(args.url))
            print(json.dumps(response, indent=4))
        elif args.action == "post":
            response = client.post(args.url, json=body)
            check_response_status(response)
            if not args.quiet:
                print(json.dumps(response.json(), indent=4))
        elif args.action == "put":
            response = client.put(args.url, json=body)
            check_response_status(response)
            if not args.quiet:
                print(json.dumps(response.json(), indent=4))
        elif args.action == "patch":
            response = client.patch(args.url, json=body)
            check_response_status(response)
            if not args.quiet:
                print(json.dumps(response.json(), indent=4))
    except HTTPError as e:
        if not args.quiet:
            print(json.dumps(e.response.json()))
        exit(1)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("get", "get_pages", "post", "put", "patch"))
    parser.add_argument("url", type=str)

    parser.add_argument(
        "--json_body",
        "-j",
        type=str,
        default=None,
        help="JSON data (string-encoded) to be added to the request body.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        default=False,
        action="store_true",
        help="Don't print the response data for POST, PUT, and PATCH requests.",
    )

    parser.add_argument("--base_url", "-u", type=str, default="https://autograder.io/")
    parser.add_argument(
        "--token_file",
        "-t",
        type=str,
        default=".agtoken",
        help="A filename or a path describing where to find the API token. "
        "If a filename, searches the current directory and each "
        "directory up to and including the current user's home "
        "directory until the file is found.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
