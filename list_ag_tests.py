#! /usr/bin/env python3

import argparse
import json
from urllib.parse import urljoin

import requests

import utils


def main():
    args = parse_args()

    url = urljoin(args.base_url,
                  f'/api/projects/{args.project_id}/ag_test_suites/')
    response = requests.get(url)
    response.raise_for_status()

    if args.dump_json:
        print(json.dumps(response.json(), indent=4))
        exit(0)

    for suite in response.json():
        print(f"{suite['name']}: {suite['pk']}")

        for case in suite['ag_test_cases']:
            print(f"{' ' * 2} {case['name']}: {case['pk']}")
            for cmd in case['ag_test_commands']:
                print(f"{' ' * 4} {cmd['name']}: {cmd['pk']}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Print the names and IDs of AG test suites, cases, "
                    "and commands belonging to a project.")
    parser.add_argument('project_id')

    parser.add_argument(
        '--dump_json', '-j',
        action='store_true', default=False,
        help='Only print a full JSON dump of all AG test suites, cases, '
             'and commands belonging to the requested project.')

    parser.add_argument(
        '--base_url', '-u', type=str,
        default='https://autograder.io/',
        help="""The scheme and hostname to use for all requests.
                This is mainly used for testing on a
                locally-deployed instance of the autograder API.""")
    parser.add_argument(
        '--token_file', '-t', type=str, default='.agtoken',
        help="A filename or a path describing where to find the API token. "
             "If a filename, searches the current directory and each "
             "directory up to and including the current user's home "
             "directory until the file is found.")

    return parser.parse_args()


if __name__ == '__main__':
    main()
