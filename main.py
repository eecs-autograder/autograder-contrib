import argparse
import json

from ag_contrib.http_client import check_response_status, HTTPClient


def main():
    args = parse_args()
    body = {} if args.json_body is None else json.loads(args.json_body)

    client = HTTPClient.make_default(
        token_filename=args.token_file, base_url=args.base_url)
    if args.action == 'get':
        response = client.get(args.url)
        check_response_status(response)
        print(json.dumps(response.json(), indent=4))
    elif args.action == 'get_pages':
        response = list(client.get_paginated(args.url))
        print(json.dumps(response.json(), indent=4))
    elif args.action == 'post':
        response = client.post(args.url, json=body)
    elif args.action == 'put':
        response = client.put(args.url, json=body)
    elif args.action == 'patch':
        response = client.patch(args.url, json=body)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'action',
        choices=('get', 'get_pages', 'post', 'put', 'patch'))
    parser.add_argument('url', type=str)

    parser.add_argument(
        '--json_body', '-j',
        type=str,
        default=None,
        help='JSON-encoded string data to be added to the request body.'
    )

    parser.add_argument('--base_url', '-u', type=str,
                        default='https://autograder.io/')
    parser.add_argument(
        '--token_file', '-t', type=str, default='.agtoken',
        help="A filename or a path describing where to find the API token. "
             "If a filename, searches the current directory and each "
             "directory up to and including the current user's home "
             "directory until the file is found.")
    return parser.parse_args()


if __name__ == '__main__':
    main()
