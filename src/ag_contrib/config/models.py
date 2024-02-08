from __future__ import annotations

from pathlib import Path
from typing import Literal, TypeAlias
from pydantic import BaseModel

from ag_contrib.config.generated import schema as ag_schema


def _get_builtin_cmd_fdbk_presets():
    return BUILTIN_CMD_FDBK_PRESETS


def _get_builtin_test_suite_fdbk_presets():
    return BUILTIN_TEST_SUITE_FDBK_PRESETS


class AGConfig(BaseModel):
    project: ProjectConfig
    feedback_presets: dict[str, ag_schema.AGTestCommandFeedbackConfig] = (
        _get_builtin_cmd_fdbk_presets()
    )
    feedback_presets_test_suite_setup: dict[str, ag_schema.AGTestSuiteFeedbackConfig] = (
        _get_builtin_test_suite_fdbk_presets()
    )
    docker_images: dict[str, DockerImage] = {}


class ProjectConfig(BaseModel):
    settings: ag_schema.CreateProject
    course: ag_schema.CreateCourse
    student_files: list[ag_schema.ExpectedStudentFile] = []
    instructor_files: list[InstructorFileConfig] = []
    test_suites: list[TestSuiteConfig] = []


class DockerImage(BaseModel):
    build_dir: Path
    include: list[Path] = []
    exclude: list[Path] = []


class InstructorFileConfig(BaseModel):
    local_path: Path

    @property
    def name(self) -> str:
        return self.local_path.name


class StudentFileConfig(BaseModel):
    pattern: str
    min_num_matches: int = 1
    max_num_matches: int = 1


class TestSuiteConfig(BaseModel):
    name: str
    instructor_files_needed: list[str] = []
    read_only_instructor_files: bool = True
    student_files_needed: list[str] = []

    allow_network_access: bool = False
    deferred: bool = False
    sandbox_docker_image: str = 'Default'

    setup_suite_cmd: str = 'echo "Configure your setup command here. Set to empty string to not use a setup command"'
    setup_suite_cmd_name: str = 'Setup'
    reject_submission_if_setup_fails: bool = False

    normal_fdbk_config: str | ag_schema.AGTestSuiteFeedbackConfig = 'public'
    ultimate_submission_fdbk_config: str | ag_schema.AGTestSuiteFeedbackConfig = 'public'
    past_limit_submission_fdbk_config: str | ag_schema.AGTestSuiteFeedbackConfig = 'public'
    staff_viewer_fdbk_config: str | ag_schema.AGTestSuiteFeedbackConfig = 'public'

    test_cases: list[SingleCmdTestCaseConfig | MultiCmdTestCaseConfig] = []


class TestCaseAdvancedFdbkConfig(BaseModel):
    normal_fdbk_config: ag_schema.AGTestCaseFeedbackConfig = {
        'visible': True,
        'show_individual_commands': True,
    }
    ultimate_submission_fdbk_config: ag_schema.AGTestCaseFeedbackConfig = {
        'visible': True,
        'show_individual_commands': True,
    }
    past_limit_submission_fdbk_config: ag_schema.AGTestCaseFeedbackConfig = {
        'visible': True,
        'show_individual_commands': True,
    }
    staff_viewer_fdbk_config: ag_schema.AGTestCaseFeedbackConfig = {
        'visible': True,
        'show_individual_commands': True,
    }


class MultiCmdTestCaseConfig(BaseModel):
    name: str
    type: Literal['multi_cmd']
    repeat: list[dict[str, object]] = []
    advanced_feedback: TestCaseAdvancedFdbkConfig = TestCaseAdvancedFdbkConfig()
    commands: list[MultiCommandConfig] = []

    def do_repeat(self) -> list[MultiCmdTestCaseConfig]:
        raise NotImplementedError

    def to_json(self) -> ag_schema.AGTestCase:
        raise NotImplementedError


class MultiCommandConfig(BaseModel):
    name: str
    cmd: str

    input: StdinSettings
    return_code: MultiCmdReturnCodeCheckSettings
    output_diff: MultiCmdDiffSettings
    feedback: CommandFeedbackSettings
    resources: ResourceLimits

    repeat: list[dict[str, object]] = []


class SingleCmdTestCaseConfig(BaseModel):
    name: str
    type: Literal['default', 'single_cmd']

    input: StdinSettings
    return_code: SingleCmdReturnCodeCheckSettings
    output_diff: SingleCmdDiffSettings
    feedback: CommandFeedbackSettings
    resources: ResourceLimits

    repeat: list[dict[str, object]] = []

    def do_repeat(self) -> list[SingleCmdTestCaseConfig]:
        raise NotImplementedError

    def to_json(self) -> ag_schema.AGTestCase:
        raise NotImplementedError


class StdinSettings(BaseModel):
    stdin_source: ag_schema.StdinSource = 'none'
    stdin_text: str = ""
    stdin_instructor_file: str | None = None


class MultiCmdReturnCodeCheckSettings(BaseModel):
    expected_return_code: ag_schema.ExpectedReturnCode = 'none'
    points_for_correct_return_code: int = 0
    deduction_for_wrong_return_code: int = 0


class SingleCmdReturnCodeCheckSettings(BaseModel):
    expected_return_code: ag_schema.ExpectedReturnCode = 'none'
    points_for_correct_return_code: int = 0


class MultiCmdDiffSettings(BaseModel):
    expected_stdout_source: ag_schema.ExpectedOutputSource = 'none'
    expected_stdout_text: str = ""
    expected_stdout_instructor_file: str | None = None
    points_for_correct_stdout: int = 0
    deduction_for_wrong_stdout: int = 0

    expected_stderr_source: ag_schema.ExpectedOutputSource = 'none'
    expected_stderr_text: str = ""
    expected_stderr_instructor_file: str | None = None
    points_for_correct_stderr: int = 0
    deduction_for_wrong_stderr: int = 0

    ignore_case: bool = False
    ignore_whitespace: bool = False
    ignore_whitespace_changes: bool = False
    ignore_blank_lines: bool = False


class SingleCmdDiffSettings(BaseModel):
    expected_stdout_source: ag_schema.ExpectedOutputSource = 'none'
    expected_stdout_text: str = ""
    expected_stdout_instructor_file: str | None = None
    points_for_correct_stdout: int = 0

    expected_stderr_source: ag_schema.ExpectedOutputSource = 'none'
    expected_stderr_text: str = ""
    expected_stderr_instructor_file: str | None = None
    points_for_correct_stderr: int = 0

    ignore_case: bool = False
    ignore_whitespace: bool = False
    ignore_whitespace_changes: bool = False
    ignore_blank_lines: bool = False


class CommandFeedbackSettings(BaseModel):
    normal_fdbk_config: ag_schema.AGTestCommandFeedbackConfig | str = "pass/fail"
    first_failed_test_normal_fdbk_config: ag_schema.AGTestCommandFeedbackConfig | str | None = None
    ultimate_submission_fdbk_config: ag_schema.AGTestCommandFeedbackConfig | str = "pass/fail"
    past_limit_submission_fdbk_config: ag_schema.AGTestCommandFeedbackConfig | str = "private"
    staff_viewer_fdbk_config: ag_schema.AGTestCommandFeedbackConfig | str = "public"


class ResourceLimits(BaseModel):
    time_limit: int = 10
    virtual_memory_limit: int | None = None
    block_process_spawn: bool = False


BUILTIN_TEST_SUITE_FDBK_PRESETS = {
    'public': ag_schema.AGTestSuiteFeedbackConfig(
        visible=True,
        show_individual_tests=True,
        show_setup_return_code=True,
        show_setup_timed_out=True,
        show_setup_stdout=True,
        show_setup_stderr=True,
    ),
    'pass/fail': ag_schema.AGTestSuiteFeedbackConfig(
        visible=True,
        show_individual_tests=True,
        show_setup_return_code=True,
        show_setup_timed_out=True,
        show_setup_stdout=False,
        show_setup_stderr=False,
    ),
    'private': ag_schema.AGTestSuiteFeedbackConfig(
        visible=True,
        show_individual_tests=True,
        show_setup_return_code=False,
        show_setup_timed_out=False,
        show_setup_stdout=False,
        show_setup_stderr=False,
    ),
}


BUILTIN_CMD_FDBK_PRESETS = {
    "pass/fail": ag_schema.AGTestCommandFeedbackConfig(
        visible=True,
        return_code_fdbk_level="correct_or_incorrect",
        stdout_fdbk_level="correct_or_incorrect",
        stderr_fdbk_level="correct_or_incorrect",
        show_points=True,
        show_actual_return_code=False,
        show_actual_stdout=False,
        show_actual_stderr=False,
        show_whether_timed_out=False,
    ),
    "pass/fail+timeout": ag_schema.AGTestCommandFeedbackConfig(
        visible=True,
        return_code_fdbk_level="correct_or_incorrect",
        stdout_fdbk_level="correct_or_incorrect",
        stderr_fdbk_level="correct_or_incorrect",
        show_points=True,
        show_actual_return_code=False,
        show_actual_stdout=False,
        show_actual_stderr=False,
        show_whether_timed_out=True,
    ),
    "pass/fail+exit_status": ag_schema.AGTestCommandFeedbackConfig(
        visible=True,
        return_code_fdbk_level="correct_or_incorrect",
        stdout_fdbk_level="correct_or_incorrect",
        stderr_fdbk_level="correct_or_incorrect",
        show_points=True,
        show_actual_return_code=True,
        show_actual_stdout=False,
        show_actual_stderr=False,
        show_whether_timed_out=True,
    ),
    "pass/fail+output": ag_schema.AGTestCommandFeedbackConfig(
        visible=True,
        return_code_fdbk_level="correct_or_incorrect",
        stdout_fdbk_level="correct_or_incorrect",
        stderr_fdbk_level="correct_or_incorrect",
        show_points=True,
        show_actual_return_code=False,
        show_actual_stdout=True,
        show_actual_stderr=True,
        show_whether_timed_out=False,
    ),
    "pass/fail+diff": ag_schema.AGTestCommandFeedbackConfig(
        visible=True,
        return_code_fdbk_level="correct_or_incorrect",
        stdout_fdbk_level="expected_and_actual",
        stderr_fdbk_level="expected_and_actual",
        show_points=True,
        show_actual_return_code=False,
        show_actual_stdout=False,
        show_actual_stderr=False,
        show_whether_timed_out=False,
    ),
    "private": ag_schema.AGTestCommandFeedbackConfig(
        visible=True,
        return_code_fdbk_level="no_feedback",
        stdout_fdbk_level="no_feedback",
        stderr_fdbk_level="no_feedback",
        show_points=False,
        show_actual_return_code=False,
        show_actual_stdout=False,
        show_actual_stderr=False,
        show_whether_timed_out=False,
    ),
    "public": ag_schema.AGTestCommandFeedbackConfig(
        visible=True,
        return_code_fdbk_level="expected_and_actual",
        stdout_fdbk_level="expected_and_actual",
        stderr_fdbk_level="expected_and_actual",
        show_points=True,
        show_actual_return_code=True,
        show_actual_stdout=True,
        show_actual_stderr=True,
        show_whether_timed_out=True,
    ),
}
