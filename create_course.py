#! /usr/bin/env python3

import argparse
import os
import requests
from urllib.parse import urljoin

import utils


def main():
    args = parse_args()

    api_token = None
    try:
        api_token = utils.get_api_token(args.token_file)
    except utils.TokenFileNotFound as e:
        print(e)
        exit(1)

    response = requests.post(
        urljoin(args.base_url, f'/api/courses/'),
        json={
            'name': args.course_name,
            'semester': args.course_semester,
            'year': args.course_year
        },
        headers={'Authorization': f'Token {api_token}'}
    )

    utils.check_response_status(response)
    print('New course created successfully')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('course_name')
    parser.add_argument('course_semester',
                        choices=['Winter', 'Spring', 'Summer', 'Fall'])
    parser.add_argument('course_year', type=int)

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
