import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from ag_contrib.config.models import (
    AGConfig,
    AGTestCommandFeedbackConfig,
    CommandConfig,
    TestCaseConfig,
    TestSuiteConfig,
)
from ag_contrib.http_client import HTTPClient, check_response_status
from ag_contrib.utils import get_api_token

# HACK
g_feedback_presets: dict[str, AGTestCommandFeedbackConfig] = {}


def save_project(config_file: str, *, base_url: str, token_file: str):
    with open(config_file) as f:
        config = AGConfig.model_validate(yaml.load(f, Loader=Loader))

    global g_feedback_presets
    g_feedback_presets = config.feedback_presets

    client = HTTPClient(get_api_token(token_file), base_url)

    course_data = config.project.course
    course_response = client.get(
        f"/api/course/{course_data.name}/{course_data.semester.value}/{course_data.year}/"
    )
    check_response_status(course_response)
    course = course_response.json()

    projects_response = client.get(f'/api/courses/{course["pk"]}/projects/')
    check_response_status(projects_response)
    projects = projects_response.json()
    # print(projects)

    project = next((p for p in projects if p["name"] == config.project.settings.name), None)
    if project is None:
        print(f"Creating project {config.project.settings.name}...")
        response = client.post(
            f'/api/courses/{course["pk"]}/projects/', json={"name": config.project.settings.name}
        )
        check_response_status(response)
        project = response.json()
        print("Project created")

    print("Checking instructor files...")
    instructor_files_response = client.get(f'/api/projects/{project["pk"]}/instructor_files/')
    check_response_status(instructor_files_response)
    instructor_files = {item["name"]: item for item in instructor_files_response.json()}

    for file_config in config.project.instructor_files:
        print("* Checking", file_config.name, "...")
        if file_config.name in instructor_files:
            response = client.put(
                f'/api/instructor_files/{instructor_files[file_config.name]["pk"]}/content/',
                files={"file_obj": open(file_config.local_path, "rb")},
            )
            check_response_status(response)
            print("  Updated", file_config.name, "from", file_config.local_path)
        else:
            response = client.post(
                f'/api/projects/{project["pk"]}/instructor_files/',
                files={"file_obj": open(file_config.local_path, "rb")},
            )
            check_response_status(response)
            print("  Created", file_config.name, "from", file_config.local_path)

    print("Checking student files")
    student_files_response = client.get(f'/api/projects/{project["pk"]}/expected_student_files/')
    check_response_status(student_files_response)
    student_files = {item["pattern"]: item for item in student_files_response.json()}

    for student_file_config in config.project.student_files:
        print("* Checking", student_file_config.pattern, "...")
        if student_file_config.pattern in student_files:
            response = client.patch(
                f'/api/expected_student_files/{student_files[student_file_config.pattern]["pk"]}/',
                json=student_file_config.model_dump(exclude_unset=True),
            )
            check_response_status(response)
            print("  Updated", student_file_config.pattern)
        else:
            response = client.post(
                f'/api/projects/{project["pk"]}/expected_student_files/',
                json=student_file_config.model_dump(exclude_unset=True),
            )
            check_response_status(response)
            print("  Created", student_file_config.pattern)

    print("Checking test suites")
    test_suites_response = client.get(f'/api/projects/{project["pk"]}/ag_test_suites/')
    check_response_status(test_suites_response)
    test_suites = {item["name"]: item for item in test_suites_response.json()}

    for suite_data in config.project.test_suites:
        print("* Checking test suite", suite_data.name, "...")
        if suite_data.name in test_suites:
            response = client.patch(
                f'/api/ag_test_suites/{test_suites[suite_data.name]["pk"]}/',
                json=suite_data.model_dump(
                    exclude_unset=True,
                    exclude={"test_cases", "student_files_needed", "instructor_files_needed"},
                )
                | {
                    "student_files_needed": [
                        student_files[pattern] for pattern in suite_data.student_files_needed
                    ],
                    "instructor_files_needed": [
                        instructor_files[name] for name in suite_data.instructor_files_needed
                    ],
                },
            )
            check_response_status(response)
            print("  Updated", suite_data.name)
        else:
            response = client.post(
                f'/api/projects/{project["pk"]}/ag_test_suites/',
                json=suite_data.model_dump(
                    exclude_unset=True,
                    exclude={"test_cases", "student_files_needed", "instructor_files_needed"},
                )
                | {
                    "student_files_needed": [
                        student_files[pattern] for pattern in suite_data.student_files_needed
                    ],
                    "instructor_files_needed": [
                        instructor_files[name] for name in suite_data.instructor_files_needed
                    ],
                },
            )
            check_response_status(response)
            test_suites[suite_data.name] = response.json()
            print("  Created", suite_data.name)

        test_cases = {test["name"]: test for test in test_suites[suite_data.name]["ag_test_cases"]}
        for test_data in suite_data.test_cases:
            if test_data.repeat:
                repeat_test_case(
                    test_data.repeat,
                    client,
                    suite_data,
                    test_data,
                    test_suites=test_suites,
                    test_cases=test_cases,
                    instructor_files=instructor_files,
                )
            else:
                create_or_update_test(
                    client,
                    suite_data,
                    test_data,
                    test_suites=test_suites,
                    test_cases=test_cases,
                    instructor_files=instructor_files,
                )


def get_instr_file(name: str | None, instr_files: dict[str, dict]):
    if name is None:
        return None

    return instr_files[name]


def get_fdbk_conf(val: str | AGTestCommandFeedbackConfig | None) -> dict | None:
    if val is None:
        return None

    if isinstance(val, str):
        if val not in g_feedback_presets:
            print(f'Feedback preset "{val}" not found.')
        return g_feedback_presets[val].model_dump(mode="json")

    return val


def create_or_update_test(
    client: HTTPClient,
    suite_data: TestSuiteConfig,
    test_data: TestCaseConfig,
    *,
    test_suites: dict[str, dict],
    test_cases: dict[str, dict],
    instructor_files: dict[str, dict],
) -> None:
    _create_or_update_test_shallow(
        client,
        suite_data,
        test_data,
        test_suites=test_suites,
        test_cases=test_cases,
    )

    commands = {cmd["name"]: cmd for cmd in test_cases[test_data.name]["ag_test_commands"]}
    for cmd_data in test_data.commands:
        if cmd_data.repeat:
            repeat_command(
                cmd_data.repeat,
                client,
                test_data,
                cmd_data,
                test_cases=test_cases,
                commands=commands,
                instructor_files=instructor_files,
            )
        else:
            create_or_update_command(
                client,
                test_data,
                cmd_data,
                test_cases=test_cases,
                commands=commands,
                instructor_files=instructor_files,
            )


def _create_or_update_test_shallow(
    client: HTTPClient,
    suite_data: TestSuiteConfig,
    test_data: TestCaseConfig,
    *,
    test_suites: dict[str, dict],
    test_cases: dict[str, dict],
) -> None:
    request_body = test_data.model_dump(exclude_unset=True, exclude={"commands", "repeat"})

    print("  * Checking test case", test_data.name, "...")
    if test_data.name in test_cases:
        response = client.patch(
            f'/api/ag_test_cases/{test_cases[test_data.name]["pk"]}/', json=request_body
        )
        check_response_status(response)
        print("    Updated", test_data.name)
    else:
        response = client.post(
            f'/api/ag_test_suites/{test_suites[suite_data.name]["pk"]}/ag_test_cases/',
            json=request_body,
        )
        check_response_status(response)
        test_cases[test_data.name] = response.json()
        print("    Created", test_data.name)


def create_or_update_command(
    client: HTTPClient,
    test_data: TestCaseConfig,
    cmd_data: CommandConfig,
    *,
    test_cases: dict[str, dict],
    commands: dict[str, dict],
    instructor_files: dict[str, dict],
) -> None:
    exclude_fields = [
        "stdin_instructor_file",
        "expected_stdout_instructor_file",
        "expected_stderr_instructor_file",
        "normal_fdbk_config",
        "first_failed_test_normal_fdbk_config",
        "ultimate_submission_fdbk_config",
        "past_limit_submission_fdbk_config",
        "staff_viewer_fdbk_config",
        "repeat",
    ]

    stitched_data = {
        "stdin_instructor_file": get_instr_file(cmd_data.stdin_instructor_file, instructor_files),
        "expected_stdout_instructor_file": get_instr_file(
            cmd_data.expected_stdout_instructor_file, instructor_files
        ),
        "expected_stderr_instructor_file": get_instr_file(
            cmd_data.expected_stderr_instructor_file, instructor_files
        ),
        "normal_fdbk_config": get_fdbk_conf(cmd_data.normal_fdbk_config),
        "first_failed_test_normal_fdbk_config": get_fdbk_conf(
            cmd_data.first_failed_test_normal_fdbk_config
        ),
        "ultimate_submission_fdbk_config": get_fdbk_conf(cmd_data.ultimate_submission_fdbk_config),
        "past_limit_submission_fdbk_config": get_fdbk_conf(
            cmd_data.past_limit_submission_fdbk_config
        ),
        "staff_viewer_fdbk_config": get_fdbk_conf(cmd_data.staff_viewer_fdbk_config),
    }

    print("    * Checking command", cmd_data.name, "...")

    request_body = (
        cmd_data.model_dump(mode="json", exclude_unset=True, exclude=exclude_fields)
        | stitched_data
    )

    if cmd_data.name in commands:
        response = client.patch(
            f'/api/ag_test_commands/{commands[cmd_data.name]["pk"]}/',
            json=request_body,
        )
        check_response_status(response)
        print("      Updated", cmd_data.name)
    else:
        response = client.post(
            f'/api/ag_test_cases/{test_cases[test_data.name]["pk"]}/ag_test_commands/',
            json=request_body,
        )
        check_response_status(response)
        commands[cmd_data.name] = response.json()
        print("      Created", cmd_data.name)


def repeat_test_case(
    substitutions: list[dict[str, object]],
    client: HTTPClient,
    suite_data: TestSuiteConfig,
    test_data: TestCaseConfig,
    *,
    test_suites: dict[str, dict],
    test_cases: dict[str, dict],
    instructor_files: dict[str, dict],
):
    print(f"  Repeating test case {test_data.name}")
    for sub in substitutions:
        new_test_data = test_data.model_copy(deep=True)
        new_test_data.name = apply_substitutions(test_data.name, sub)

        _create_or_update_test_shallow(
            client,
            suite_data,
            new_test_data,
            test_suites=test_suites,
            test_cases=test_cases,
        )

        commands = {cmd["name"]: cmd for cmd in test_cases[new_test_data.name]["ag_test_commands"]}
        for cmd_data in test_data.commands:
            new_cmd_data = cmd_data.model_copy(deep=True)
            new_cmd_data.name = apply_substitutions(new_cmd_data.name, sub)
            new_cmd_data.cmd = apply_substitutions(new_cmd_data.cmd, sub)
            if new_cmd_data.stdin_instructor_file is not None:
                new_cmd_data.stdin_instructor_file = apply_substitutions(
                    new_cmd_data.stdin_instructor_file, sub
                )

            if new_cmd_data.expected_stdout_instructor_file is not None:
                new_cmd_data.expected_stdout_instructor_file = apply_substitutions(
                    new_cmd_data.expected_stdout_instructor_file, sub
                )

            if new_cmd_data.expected_stderr_instructor_file is not None:
                new_cmd_data.expected_stderr_instructor_file = apply_substitutions(
                    new_cmd_data.expected_stderr_instructor_file, sub
                )

            if new_cmd_data.repeat:
                repeat_command(
                    new_cmd_data.repeat,
                    client,
                    new_test_data,
                    new_cmd_data,
                    test_cases=test_cases,
                    commands=commands,
                    instructor_files=instructor_files,
                )
            else:
                create_or_update_command(
                    client,
                    new_test_data,
                    new_cmd_data,
                    test_cases=test_cases,
                    commands=commands,
                    instructor_files=instructor_files,
                )


def repeat_command(
    substitutions: list[dict[str, object]],
    client: HTTPClient,
    test_data: TestCaseConfig,
    cmd_data: CommandConfig,
    *,
    test_cases: dict[str, dict],
    commands: dict[str, dict],
    instructor_files: dict[str, dict],
) -> None:
    print(f"    Repeating command {cmd_data.name}")
    for sub in substitutions:
        new_name = apply_substitutions(cmd_data.name, sub)
        new_cmd = apply_substitutions(cmd_data.cmd, sub)

        new_cmd_data = cmd_data.model_copy(deep=True)
        new_cmd_data.name = new_name
        new_cmd_data.cmd = new_cmd

        if new_cmd_data.stdin_instructor_file is not None:
            new_cmd_data.stdin_instructor_file = apply_substitutions(
                new_cmd_data.stdin_instructor_file, sub
            )

        if new_cmd_data.expected_stdout_instructor_file is not None:
            new_cmd_data.expected_stdout_instructor_file = apply_substitutions(
                new_cmd_data.expected_stdout_instructor_file, sub
            )

        if new_cmd_data.expected_stderr_instructor_file is not None:
            new_cmd_data.expected_stderr_instructor_file = apply_substitutions(
                new_cmd_data.expected_stderr_instructor_file, sub
            )

        create_or_update_command(
            client,
            test_data,
            new_cmd_data,
            test_cases=test_cases,
            commands=commands,
            instructor_files=instructor_files,
        )


def apply_substitutions(string: str, sub: dict[str, object]) -> str:
    for placeholder, replacement in sub.items():
        string = string.replace(placeholder, str(replacement))

    return string
