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

    http = utils.HTTPClient(api_token, args.base_url)
    response = http.get_paginated(
        f'/api/projects/{args.project_pk}/all_ultimate_submission_results/')
    ultimate_submissions_by_group = {
        item['group']['pk']: item for item in response}

    handgrading_results = http.get_paginated(
        f'/api/projects/{args.project_pk}/handgrading_results/')

    # print(len(ultimate_submissions_by_group))
    # print(len(handgrading_results))

    for group_with_handgrading in handgrading_results:
        if group_with_handgrading['handgrading_result'] is None:
            continue
        full_hand_result = http.get(
            f'/api/groups/{group_with_handgrading["pk"]}/handgrading_result/')
        utils.check_response_status(full_hand_result)
        ultimate_pk = ultimate_submissions_by_group[
            group_with_handgrading['pk']]['ultimate_submission']['pk']
        if full_hand_result.json()['submission'] != ultimate_pk:
            print(group_with_handgrading['pk'],
                  group_with_handgrading['member_names'])


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('project_pk', type=int)

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
