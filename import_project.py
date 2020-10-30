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


    project_json = _load_json('project.json', args.input_dir)
    ag_test_json = _load_json('ag_tests.json', args.input_dir)
    mutation_test_json = _load_json('mutation_tests.json', args.input_dir)
    handgrading_json = _load_json('handgrading.json', args.input_dir)

    sandbox_images = _load_sandbox_images(client, args.course_id)

    project = _create_project(client, args.course_id, project_json, args.project_name)
    instructor_files_dir = os.path.join(args.input_dir, 'instructor_files')
    instructor_files = _import_instructor_files(client, project['pk'], instructor_files_dir)
    expected_student_files = _create_expected_student_files(client, project['pk'], project_json)
    ag_tests = _create_ag_tests(
        client, project['pk'], sandbox_images,
        instructor_files, expected_student_files, ag_test_json)
    mutation_tests = _create_mutation_test_suites(
        client, project['pk'], sandbox_images, instructor_files,
        expected_student_files, mutation_test_json)

    if handgrading_json is not None:
        _create_handgrading_rubric(client, project['pk'], handgrading_json)


def _load_json(filename, input_dir):
    with open(os.path.join(input_dir, filename)) as f:
        return json.load(f)


def _create_project(client, course_id, project_json, project_name=None):
    request_body = dict(project_json)
    request_body.pop('expected_student_files')
    if project_name is not None:
        request_body['name'] = project_name
    response = client.post(f'/api/courses/{course_id}/projects/', json=request_body)
    check_response_status(response)
    return response.json()


def _load_sandbox_images(client, course_id):
    # Update when we deploy 4.0 to include course-linked images
    global_images_response = client.get('/api/sandbox_docker_images/')
    course_images_response = client.get(f'/api/courses/{course_id}/sandbox_docker_images/')

    check_response_status(global_images_response)
    check_response_status(course_images_response)

    available_images = global_images_response.json() + course_images_response.json()

    return {item['display_name']: item for item in available_images}


def _import_instructor_files(client, project_pk, instructor_files_dir):
    data = {}
    for filename in os.listdir(instructor_files_dir):
        with open(os.path.join(instructor_files_dir, filename), 'rb') as f:
            response = client.post(
                f'/api/projects/{project_pk}/instructor_files/',
                files={'file_obj': f}
            )
            check_response_status(response)

        data[filename] = response.json()

    return data


def _create_expected_student_files(client, project_pk, project_json):
    data = {}
    for expected_file in project_json['expected_student_files']:
        response = client.post(
            f'/api/projects/{project_pk}/expected_student_files/',
            json=expected_file
        )
        check_response_status(response)
        data[expected_file['pattern']] = response.json()

    return data


def _create_ag_tests(
    client, project_pk, sandbox_docker_images,
    instructor_files, expected_student_files, ag_test_json
):
    result = []
    for suite_json in ag_test_json:
        request_body = dict(suite_json)
        request_body.pop('ag_test_cases')
        request_body['sandbox_docker_image'] = (
            sandbox_docker_images[suite_json['sandbox_docker_image']['display_name']])
        request_body['instructor_files_needed'] = [
            instructor_files[file_json['name']]
            for file_json in suite_json['instructor_files_needed']
        ]
        request_body['student_files_needed'] = [
            expected_student_files[file_json['pattern']]
            for file_json in suite_json['student_files_needed']
        ]

        suite_response = client.post(
            f'/api/projects/{project_pk}/ag_test_suites/', json=request_body)
        check_response_status(suite_response)
        suite = suite_response.json()
        result.append(suite)

        for test_json in suite_json['ag_test_cases']:
            test_request_body = dict(test_json)
            test_request_body.pop('ag_test_commands')
            test_response = client.post(
                f'/api/ag_test_suites/{suite["pk"]}/ag_test_cases/',
                json=test_request_body)
            check_response_status(test_response)
            test = test_response.json()
            suite['ag_test_cases'].append(test)

            for cmd_json in test_json['ag_test_commands']:
                cmd_request_body = dict(cmd_json)
                if cmd_json['stdin_instructor_file'] is not None:
                    cmd_request_body['stdin_instructor_file'] = instructor_files[
                        cmd_json['stdin_instructor_file']['name']
                    ]
                if cmd_json['expected_stdout_instructor_file'] is not None:
                    cmd_request_body['expected_stdout_instructor_file'] = instructor_files[
                        cmd_json['expected_stdout_instructor_file']['name']
                    ]
                if cmd_json['expected_stderr_instructor_file'] is not None:
                    cmd_request_body['expected_stderr_instructor_file'] = instructor_files[
                        cmd_json['expected_stderr_instructor_file']['name']
                    ]

                cmd_response = client.post(
                    f'/api/ag_test_cases/{test["pk"]}/ag_test_commands/',
                    json=cmd_request_body
                )
                check_response_status(cmd_response)

                test['ag_test_commands'].append(cmd_response.json())

    return result


def _create_mutation_test_suites(
    client, project_pk, sandbox_docker_images,
    instructor_files, expected_student_files, mutation_test_json
):
    result = []
    for suite_json in mutation_test_json:
        request_body = dict(suite_json)
        request_body['sandbox_docker_image'] = (
            sandbox_docker_images[suite_json['sandbox_docker_image']['display_name']])
        request_body['instructor_files_needed'] = [
            instructor_files[file_json['name']]
            for file_json in suite_json['instructor_files_needed']
        ]
        request_body['student_files_needed'] = [
            expected_student_files[file_json['pattern']]
            for file_json in suite_json['student_files_needed']
        ]

        suite_response = client.post(
            f'/api/projects/{project_pk}/mutation_test_suites/', json=request_body)
        check_response_status(suite_response)
        suite = suite_response.json()
        result.append(suite)

    return result


def _create_handgrading_rubric(client, project_pk, handgrading_json):
    rubric_request_body = dict(handgrading_json)
    rubric_request_body.pop('criteria')
    rubric_request_body.pop('annotations')

    rubric_response = client.post(
        f'/api/projects/{project_pk}/handgrading_rubric/',
        json=rubric_request_body
    )
    check_response_status(rubric_response)
    rubric = rubric_response.json()

    for criterion_json in handgrading_json['criteria']:
        criterion_response = client.post(
            f'/api/handgrading_rubrics/{rubric["pk"]}/criteria/',
            json=criterion_json
        )
        check_response_status(criterion_response)

    for annotation_json in handgrading_json['annotations']:
        annotation_response = client.post(
            f'/api/handgrading_rubrics/{rubric["pk"]}/annotations/',
            json=annotation_json
        )
        check_response_status(annotation_response)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('course_id', type=int, help='The course to import the project to.')
    parser.add_argument('input_dir', help='The directory to read project data from.')
    parser.add_argument('--project_name', '-n', help='The name of the new project.')

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
