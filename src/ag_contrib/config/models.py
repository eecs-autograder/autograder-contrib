from __future__ import annotations
import datetime

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ag_contrib.config.generated import schema as ag_schema


class AGConfig(BaseModel):
    project: ProjectConfig
    feedback_presets: dict[str, ag_schema.AGTestCommandFeedbackConfig] = Field(
        default_factory=lambda: BUILTIN_CMD_FDBK_PRESETS
    )
    feedback_presets_test_suite_setup: dict[str, ag_schema.AGTestSuiteFeedbackConfig] = Field(
        default_factory=lambda: BUILTIN_TEST_SUITE_FDBK_PRESETS
    )
    docker_images: dict[str, DockerImage] = {}


class ProjectConfig(BaseModel):
    name: str
    settings: ProjectSettings = Field(default_factory=lambda: ProjectSettings())
    course: CourseSelection
    student_files: list[ag_schema.CreateExpectedStudentFile] = []
    instructor_files: list[InstructorFileConfig] = []
    test_suites: list[TestSuiteConfig] = []


class CourseSelection(BaseModel):
    name: str
    semester: Literal["Fall", "Winter", "Spring", "Summer"] | None
    year: int | None


class ProjectSettings(BaseModel):
    soft_closing_time: datetime.datetime | None = (
        datetime.datetime.now().astimezone().replace(minute=0, second=0, microsecond=0)
        + datetime.timedelta(days=7)
    )
    closing_time: datetime.datetime | None = datetime.datetime.now().astimezone().replace(
        minute=0, second=0, microsecond=0
    ) + datetime.timedelta(days=7)
    anyone_with_link_can_submit: bool = False
    min_group_size: int = 1
    max_group_size: int = 1
    submission_limit_per_day: int | None = None
    allow_submissions_past_limit: bool = False
    groups_combine_daily_submissions: bool = False
    submission_limit_reset_time: str = "12:00pm"
    submission_limit_reset_timezone: str = "America/New_York"
    num_bonus_submissions: int = 0
    total_submission_limit: int | None = None
    allow_late_days: bool = False
    final_graded_submission: Literal["most_recent", "best"] = "most_recent"
    hide_final_graded_submission_fdbk: bool = False
    send_email_on_submission_received: bool = False
    send_email_on_non_deferred_tests_finished: bool = False
    use_honor_pledge: bool = False
    honor_pledge_text: str = ""


class DockerImage(BaseModel):
    build_dir: Path
    include: list[Path] = []
    exclude: list[Path] = []


class InstructorFileConfig(BaseModel):
    local_path: Path

    @property
    def name(self) -> str:
        return self.local_path.name


class TestSuiteConfig(BaseModel):
    name: str
    instructor_files_needed: list[str] = []
    read_only_instructor_files: bool = True
    student_files_needed: list[str] = []

    allow_network_access: bool = False
    deferred: bool = False
    sandbox_docker_image: str = "Default"

    setup_suite_cmd: str = (
        'echo "Configure your setup command here. Set to empty string to not use a setup command"'
    )
    setup_suite_cmd_name: str = "Setup"
    reject_submission_if_setup_fails: bool = False

    normal_fdbk_config: str | ag_schema.AGTestSuiteFeedbackConfig = "public"
    ultimate_submission_fdbk_config: str | ag_schema.AGTestSuiteFeedbackConfig = "public"
    past_limit_submission_fdbk_config: str | ag_schema.AGTestSuiteFeedbackConfig = "public"
    staff_viewer_fdbk_config: str | ag_schema.AGTestSuiteFeedbackConfig = "public"

    test_cases: list[SingleCmdTestCaseConfig | MultiCmdTestCaseConfig] = []


class MultiCmdTestCaseConfig(BaseModel):
    name: str
    type: Literal["multi_cmd"] = "multi_cmd"
    repeat: list[dict[str, object]] = []
    advanced_feedback: TestCaseAdvancedFdbkConfig = Field(
        default_factory=lambda: TestCaseAdvancedFdbkConfig()
    )
    commands: list[MultiCommandConfig] = []

    def do_repeat(self) -> list[MultiCmdTestCaseConfig]:
        new_tests: list[MultiCmdTestCaseConfig] = []
        if not self.repeat:
            new_tests.append(self)
        else:
            for substitution in self.repeat:
                new_test = self.model_copy(deep=True)
                new_test.name = apply_substitutions(new_test.name, substitution)

                for command in new_test.commands:
                    command.name = apply_substitutions(command.name, substitution)
                    command.cmd = apply_substitutions(command.cmd, substitution)

                    if '__ag_points_for_correct_return_code' in substitution:
                        command.points_for_correct_return_code = substitution['__ag_points_for_correct_return_code']

                    if '__ag_points_for_correct_stdout' in substitution:
                        command.points_for_correct_stdout = substitution['__ag_points_for_correct_stdout']

                    if '__ag_points_for_correct_stderr' in substitution:
                        command.points_for_correct_stderr = substitution['__ag_points_for_correct_stderr']

                new_test.commands = [cmd.do_repeat() for cmd in new_test.commands]

                # new_tests.append(new_test)

        raise NotImplementedError

    def to_json(self) -> ag_schema.AGTestCase:
        raise NotImplementedError


class TestCaseAdvancedFdbkConfig(BaseModel):
    normal_fdbk_config: ag_schema.AGTestCaseFeedbackConfig = {
        "visible": True,
        "show_individual_commands": True,
    }
    ultimate_submission_fdbk_config: ag_schema.AGTestCaseFeedbackConfig = {
        "visible": True,
        "show_individual_commands": True,
    }
    past_limit_submission_fdbk_config: ag_schema.AGTestCaseFeedbackConfig = {
        "visible": True,
        "show_individual_commands": True,
    }
    staff_viewer_fdbk_config: ag_schema.AGTestCaseFeedbackConfig = {
        "visible": True,
        "show_individual_commands": True,
    }


class MultiCommandConfig(BaseModel):
    name: str
    cmd: str

    input: StdinSettings = Field(default_factory=lambda: StdinSettings())
    return_code: MultiCmdReturnCodeCheckSettings = Field(
        default_factory=lambda: MultiCmdReturnCodeCheckSettings()
    )
    output_diff: MultiCmdDiffSettings = Field(default_factory=lambda: MultiCmdDiffSettings())
    feedback: CommandFeedbackSettings = Field(default_factory=lambda: CommandFeedbackSettings())
    resources: ResourceLimits = Field(default_factory=lambda: ResourceLimits())

    repeat: list[dict[str, object]] = []


class SingleCmdTestCaseConfig(BaseModel):
    name: str
    type: Literal["default", "single_cmd"] = "default"
    cmd: str

    input: StdinSettings = Field(default_factory=lambda: StdinSettings())
    return_code: SingleCmdReturnCodeCheckSettings = Field(
        default_factory=lambda: SingleCmdReturnCodeCheckSettings()
    )
    output_diff: SingleCmdDiffSettings = Field(default_factory=lambda: SingleCmdDiffSettings())
    feedback: CommandFeedbackSettings = Field(default_factory=lambda: CommandFeedbackSettings())
    resources: ResourceLimits = Field(default_factory=lambda: ResourceLimits())

    repeat: list[dict[str, object]] = []

    def do_repeat(self) -> list[SingleCmdTestCaseConfig]:
        if not self.repeat:
            return [self]

        new_tests: list[SingleCmdTestCaseConfig] = []
        for substitution in self.repeat:
            new_test = self.model_copy(deep=True)
            new_test.name = apply_substitutions(new_test.name, substitution)
            new_test.command = apply_substitutions(new_test.name, substitution)

            if '__ag_points_for_correct_return_code' in substitution:
                new_test.points_for_correct_return_code = substitution['__ag_points_for_correct_return_code']

            if '__ag_points_for_correct_stdout' in substitution:
                new_test.points_for_correct_stdout = substitution['__ag_points_for_correct_stdout']

            if '__ag_points_for_correct_stderr' in substitution:
                new_test.points_for_correct_stderr = substitution['__ag_points_for_correct_stderr']

            new_tests.append(new_test)

        return new_tests

    def to_json(self) -> ag_schema.AGTestCase:
        raise NotImplementedError


def apply_substitutions(string: str, sub: dict[str, object]) -> str:
    for placeholder, replacement in sub.items():
        string = string.replace(placeholder, str(replacement))

    return string


class StdinSettings(BaseModel):
    stdin_source: ag_schema.StdinSource = "none"
    stdin_text: str = ""
    stdin_instructor_file: str | None = None


class MultiCmdReturnCodeCheckSettings(BaseModel):
    expected_return_code: ag_schema.ExpectedReturnCode = "none"
    points_for_correct_return_code: int = 0
    deduction_for_wrong_return_code: int = 0


class SingleCmdReturnCodeCheckSettings(BaseModel):
    expected_return_code: ag_schema.ExpectedReturnCode = "none"
    points_for_correct_return_code: int = 0


class MultiCmdDiffSettings(BaseModel):
    expected_stdout_source: ag_schema.ExpectedOutputSource = "none"
    expected_stdout_text: str = ""
    expected_stdout_instructor_file: str | None = None
    points_for_correct_stdout: int = 0
    deduction_for_wrong_stdout: int = 0

    expected_stderr_source: ag_schema.ExpectedOutputSource = "none"
    expected_stderr_text: str = ""
    expected_stderr_instructor_file: str | None = None
    points_for_correct_stderr: int = 0
    deduction_for_wrong_stderr: int = 0

    ignore_case: bool = False
    ignore_whitespace: bool = False
    ignore_whitespace_changes: bool = False
    ignore_blank_lines: bool = False


class SingleCmdDiffSettings(BaseModel):
    expected_stdout_source: ag_schema.ExpectedOutputSource = "none"
    expected_stdout_text: str = ""
    expected_stdout_instructor_file: str | None = None
    points_for_correct_stdout: int = 0

    expected_stderr_source: ag_schema.ExpectedOutputSource = "none"
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
    "public": ag_schema.AGTestSuiteFeedbackConfig(
        visible=True,
        show_individual_tests=True,
        show_setup_return_code=True,
        show_setup_timed_out=True,
        show_setup_stdout=True,
        show_setup_stderr=True,
    ),
    "pass/fail": ag_schema.AGTestSuiteFeedbackConfig(
        visible=True,
        show_individual_tests=True,
        show_setup_return_code=True,
        show_setup_timed_out=True,
        show_setup_stdout=False,
        show_setup_stderr=False,
    ),
    "private": ag_schema.AGTestSuiteFeedbackConfig(
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
