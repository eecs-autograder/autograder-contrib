#! /usr/bin/env python3

import argparse
import os
import requests
from urllib.parse import urljoin


def main():
    args = parse_args()

    api_token = None
    if not os.path.isfile(args.token_file):
        print(f"Couldn't find token file: {args.token_file}")
        exit(1)

    with open(args.token_file) as f:
        api_token = f.read().strip()

    response = requests.post(
        urljoin(args.base_url, f'/api/courses/{args.course_pk}/copy/'),
        data={
            'new_name': args.new_course_name,
            'new_semester': args.new_course_semester,
            'new_year': args.new_course_year
        },
        headers={'Authorization': f'Token {api_token}'}
    )

    response.raise_for_status()
    print('New course created successfully')
    print(response.json())


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('course_pk', type=int)
    parser.add_argument('new_course_name')
    parser.add_argument('new_course_semester',
                        choices=['Winter', 'Spring', 'Summer', 'Fall'])
    parser.add_argument('new_course_year', type=int)

    parser.add_argument('--base_url', '-u', type=str,
                        default='https://autograder.io/')
    parser.add_argument('--token_file', '-t', type=str, default='./.agtoken')

    return parser.parse_args()


if __name__ == '__main__':
    main()
