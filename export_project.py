#! /usr/bin/env python3

import argparse
import json
import os

from ag_contrib.http_client import check_response_status, HTTPClient
from ag_contrib.utils import TokenFileNotFound


def main():
    args = parse_args()

    try:
        client = HTTPClient.make_default(args.token_file, args.base_url)
    except TokenFileNotFound as e:
        print(e)
        exit(1)

    instructor_files_dir = os.path.join(args.output_dir, 'instructor_files')
    os.makedirs(instructor_files_dir, exist_ok=True)

    project_json = _download_json(client, f'/api/projects/{args.project_id}/')
    ag_test_json = _download_json(
        client, f'/api/projects/{args.project_id}/ag_test_suites/')
    mutation_test_json = _download_json(
        client, f'/api/projects/{args.project_id}/student_test_suites/')

    handgrading_json = None
    if project_json['has_handgrading_rubric']:
        handgrading_json = _download_json(
            client, f'/api/projects/{args.project_id}/handgrading_rubric/')

    with open(os.path.join(args.output_dir, 'project.json'), 'w') as f:
        json.dump(
            _filter_json(
                project_json, ['has_handgrading_rubric', 'instructor_files']
            ),
            f,
            indent=4
        )

    with open(os.path.join(args.output_dir, 'ag_tests.json'), 'w') as f:
        json.dump(
            _filter_json(
                ag_test_json,
                ['ag_test_suite', 'ag_test_case',
                 'ag_test_command', 'docker_image_to_use']),
            f,
            indent=4
        )

    with open(os.path.join(args.output_dir, 'mutation_tests.json'), 'w') as f:
        json.dump(
            _filter_json(mutation_test_json, ['docker_image_to_use']),
            f, indent=4
        )

    with open(os.path.join(args.output_dir, 'handgrading.json'), 'w') as f:
        json.dump(_filter_json(handgrading_json), f, indent=4)

    for instructor_file in project_json['instructor_files']:
        response = client.get(
            f'/api/instructor_files/{instructor_file["pk"]}/content/')
        check_response_status(response)

        path = os.path.join(instructor_files_dir, instructor_file['name'])
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)


_IGNORE_KEYS = ['pk', 'course', 'last_modified', 'project']


def _download_json(client, url):
    response = client.get(url)
    check_response_status(response)
    return response.json()


def _filter_json(data, extra_ignore_keys=[], unfiltered_keys=[]):
    """
    Recursively removes non-restorable keys such as 'pk',
    'last_modified' from data.
    """
    if isinstance(data, list):
        return [_filter_json(item, extra_ignore_keys, unfiltered_keys)
                for item in data]

    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if key in _IGNORE_KEYS or key in extra_ignore_keys:
            continue

        result[key] = (
            value if key in unfiltered_keys
            else _filter_json(value, extra_ignore_keys, unfiltered_keys)
        )

    return result


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('project_id', type=int)
    parser.add_argument(
        'output_dir',
        help='The directory to store project data in. '
             'Will be created if it does not exist.'
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
