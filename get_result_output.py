#! /usr/bin/env python3

import argparse
import os
from urllib.parse import urljoin
import zipfile

import requests

import utils


def main():
    args = parse_args()
    if os.path.exists(args.archive_filename):
        print(f'File "{args.archive_filename}" already exists.')
        exit(1)

    api_token = None
    try:
        api_token = utils.get_api_token(args.token_file)
    except utils.TokenFileNotFound as e:
        print(e)
        exit(1)

    ultimate_submission_results_url = urljoin(
        args.base_url,
        f'/api/projects/{args.project_id}/all_ultimate_submission_results/'
        f'?full_results=true&include_staff={args.include_staff}')

    groups_seen = set()

    archive_dirname = args.archive_filename.split('.')[0]
    with zipfile.ZipFile(args.archive_filename, 'w') as f:
        for page in utils.page_iterator(ultimate_submission_results_url,
                                        api_token):
            for result_data in page['results']:
                if 'results' not in result_data['ultimate_submission']:
                    print('skippp')
                    continue

                group_names = '_'.join(result_data['group']['member_names'])
                if group_names in groups_seen:
                    continue
                groups_seen.add(group_names)

                print(group_names, '...', sep='', end='')

                stdout, stderr = get_stdout_and_stderr(
                    args, result_data, api_token)

                f.writestr(
                    os.path.join(archive_dirname, group_names + '_stdout'),
                    stdout)
                f.writestr(
                    os.path.join(archive_dirname, group_names + '_stderr'),
                    stderr)

                print('done')

    print(f'Output saved to {args.archive_filename}')


def parse_args():
    parser = argparse.ArgumentParser(
        'Creates a ZIP archive containing the output '
        'of an AG test suite, case, or command for all ultimate submissions.')
    parser.add_argument('project_id')

    result_arg_group = parser.add_mutually_exclusive_group(required=True)
    result_arg_group.add_argument('--ag_test_suite_id', '-a', type=int)
    result_arg_group.add_argument('--ag_test_cmd_id', '-c', type=int)

    parser.add_argument('--archive_filename', '-f', default='output.zip')

    parser.add_argument('--include_staff', '-s',
                        action='store_const', const='true', default='false')

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


def get_stdout_and_stderr(args, result_data, api_token):
    submission_pk = result_data['ultimate_submission']['pk']
    submission_result = result_data['ultimate_submission']['results']

    url_tmpl = (f'/api/submissions/{submission_pk}/{{result_type}}/'
                f'{{result_pk}}/{{stream}}/?feedback_category=max')
    if args.ag_test_suite_id:
        result_type = 'ag_test_suite_results'
        result_pk = find_ag_test_suite_result_pk(
            submission_result, args.ag_test_suite_id)
    elif args.ag_test_cmd_id:
        result_type = 'ag_test_cmd_results'
        result_pk = find_ag_test_cmd_result_pk(
            submission_result, args.ag_test_cmd_id)
    else:
        assert False

    stdout_url = url_tmpl.format(
        result_type=result_type, result_pk=result_pk, stream='stdout')
    stdout_url = urljoin(args.base_url, stdout_url)
    stderr_url = url_tmpl.format(
        result_type=result_type, result_pk=result_pk, stream='stderr')
    stderr_url = urljoin(args.base_url, stderr_url)

    stdout_response = requests.get(
        stdout_url, headers={'Authorization': f'Token {api_token}'})
    stdout_response.raise_for_status()

    stderr_response = requests.get(
        stderr_url, headers={'Authorization': f'Token {api_token}'})
    stderr_response.raise_for_status()

    return stdout_response.text, stderr_response.text


def find_ag_test_suite_result_pk(submission_result_data, ag_test_suite_pk):
    for suite_res in submission_result_data['ag_test_suite_results']:
        if suite_res['ag_test_suite_pk'] == ag_test_suite_pk:
            if (suite_res['setup_return_code'] is None
                    and not suite_res['setup_timed_out']):
                print(f'AG test suite with ID {ag_test_suite_pk} '
                      'has no setup command.')
                exit(1)

            return suite_res['pk']

    print(f'Result for AG test suite with ID {ag_test_suite_pk} not found.')
    exit(1)


def find_ag_test_cmd_result_pk(submission_result_data, ag_test_cmd_pk):
    for suite_res in submission_result_data['ag_test_suite_results']:
        for case_res in suite_res['ag_test_case_results']:
            for cmd_res in case_res['ag_test_command_results']:
                if cmd_res['ag_test_command_pk'] == ag_test_cmd_pk:
                    return cmd_res['pk']

    print(f'Result for AG test command with ID {ag_test_cmd_pk} not found.')
    exit(1)


if __name__ == '__main__':
    main()
