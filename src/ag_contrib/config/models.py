from enum import Enum
from pydantic import BaseModel, ConfigDict, FilePath

from ag_contrib.config.generated import schema as ag_schema


class CourseData(BaseModel):
    name: str
    semester: ag_schema.Semester
    year: int


class InstructorFileConfig(BaseModel):
    local_path: FilePath

    @property
    def name(self) -> str:
        return self.local_path.name


class StudentFileConfig(BaseModel):
    pattern: str
    min_num_matches: int = 1
    max_num_matches: int = 1


class StdinSource(Enum):
    none = 'none'
    text = 'text'
    instructor_file = 'instructor_file'
    setup_stdout = 'setup_stdout'
    setup_stderr = 'setup_stderr'


class ExpectedReturnCode(Enum):
    none = 'none'
    zero = 'zero'
    nonzero = 'nonzero'


class ExpectedOutputSource(Enum):
    none = 'none'
    text = 'text'
    instructor_file = 'instructor_file'


class ValueFeedbackLevel(Enum):
    no_feedback = 'no_feedback'
    correct_or_incorrect = 'correct_or_incorrect'
    expected_and_actual = 'expected_and_actual'


class AGTestCommandFeedbackConfig(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    visible: bool
    return_code_fdbk_level: ValueFeedbackLevel
    stdout_fdbk_level: ValueFeedbackLevel
    stderr_fdbk_level: ValueFeedbackLevel
    show_points: bool
    show_actual_return_code: bool
    show_actual_stdout: bool
    show_actual_stderr: bool
    show_whether_timed_out: bool


BUILTIN_FDBK_PRESETS = {
    'pass/fail': AGTestCommandFeedbackConfig(
        visible=True,
        return_code_fdbk_level=ValueFeedbackLevel.correct_or_incorrect,
        stdout_fdbk_level=ValueFeedbackLevel.correct_or_incorrect,
        stderr_fdbk_level=ValueFeedbackLevel.correct_or_incorrect,
        show_points=True,
        show_actual_return_code=False,
        show_actual_stdout=False,
        show_actual_stderr=False,
        show_whether_timed_out=False,
    ),
    'pass/fail+timeout': AGTestCommandFeedbackConfig(
        visible=True,
        return_code_fdbk_level=ValueFeedbackLevel.correct_or_incorrect,
        stdout_fdbk_level=ValueFeedbackLevel.correct_or_incorrect,
        stderr_fdbk_level=ValueFeedbackLevel.correct_or_incorrect,
        show_points=True,
        show_actual_return_code=False,
        show_actual_stdout=False,
        show_actual_stderr=False,
        show_whether_timed_out=True,
    ),
    'pass/fail+exit_status': AGTestCommandFeedbackConfig(
        visible=True,
        return_code_fdbk_level=ValueFeedbackLevel.correct_or_incorrect,
        stdout_fdbk_level=ValueFeedbackLevel.correct_or_incorrect,
        stderr_fdbk_level=ValueFeedbackLevel.correct_or_incorrect,
        show_points=True,
        show_actual_return_code=True,
        show_actual_stdout=False,
        show_actual_stderr=False,
        show_whether_timed_out=True,
    ),
    'pass/fail+output': AGTestCommandFeedbackConfig(
        visible=True,
        return_code_fdbk_level=ValueFeedbackLevel.correct_or_incorrect,
        stdout_fdbk_level=ValueFeedbackLevel.correct_or_incorrect,
        stderr_fdbk_level=ValueFeedbackLevel.correct_or_incorrect,
        show_points=True,
        show_actual_return_code=False,
        show_actual_stdout=True,
        show_actual_stderr=True,
        show_whether_timed_out=False,
    ),
    'pass/fail+diff': AGTestCommandFeedbackConfig(
        visible=True,
        return_code_fdbk_level=ValueFeedbackLevel.correct_or_incorrect,
        stdout_fdbk_level=ValueFeedbackLevel.expected_and_actual,
        stderr_fdbk_level=ValueFeedbackLevel.expected_and_actual,
        show_points=True,
        show_actual_return_code=False,
        show_actual_stdout=False,
        show_actual_stderr=False,
        show_whether_timed_out=False,
    ),
    'private': AGTestCommandFeedbackConfig(
        visible=True,
        return_code_fdbk_level=ValueFeedbackLevel.no_feedback,
        stdout_fdbk_level=ValueFeedbackLevel.no_feedback,
        stderr_fdbk_level=ValueFeedbackLevel.no_feedback,
        show_points=False,
        show_actual_return_code=False,
        show_actual_stdout=False,
        show_actual_stderr=False,
        show_whether_timed_out=False,
    ),
    'public': AGTestCommandFeedbackConfig(
        visible=True,
        return_code_fdbk_level=ValueFeedbackLevel.expected_and_actual,
        stdout_fdbk_level=ValueFeedbackLevel.expected_and_actual,
        stderr_fdbk_level=ValueFeedbackLevel.expected_and_actual,
        show_points=True,
        show_actual_return_code=True,
        show_actual_stdout=True,
        show_actual_stderr=True,
        show_whether_timed_out=True,
    )
}


class CommandConfig(BaseModel):
    name: str
    cmd: str

    stdin_source: StdinSource = StdinSource.none
    stdin_text: str = ''
    stdin_instructor_file: str | None = None

    expected_return_code: ExpectedReturnCode = ExpectedReturnCode.none

    expected_stdout_source: ExpectedOutputSource = ExpectedOutputSource.none
    expected_stdout_text: str = ''
    expected_stdout_instructor_file: str | None = None

    expected_stderr_source: ExpectedOutputSource = ExpectedOutputSource.none
    expected_stderr_text: str = ''
    expected_stderr_instructor_file: str | None = None

    ignore_case: bool = False
    ignore_whitespace: bool = False
    ignore_whitespace_changes: bool = False
    ignore_blank_lines: bool = False

    points_for_correct_return_code: int = 0
    points_for_correct_stdout: int = 0
    points_for_correct_stderr: int = 0

    deduction_for_wrong_return_code: int = 0
    deduction_for_wrong_stdout: int = 0
    deduction_for_wrong_stderr: int = 0

    normal_fdbk_config: AGTestCommandFeedbackConfig | str = 'pass/fail'
    first_failed_test_normal_fdbk_config: AGTestCommandFeedbackConfig | str | None = None
    ultimate_submission_fdbk_config: AGTestCommandFeedbackConfig | str = 'pass/fail'
    past_limit_submission_fdbk_config: AGTestCommandFeedbackConfig | str = 'private'
    staff_viewer_fdbk_config: AGTestCommandFeedbackConfig | str = 'public'

    time_limit: int = 10
    use_virtual_memory_limit: bool = False
    virtual_memory_limit: int = 500 * 10 ** 6
    block_process_spawn: bool = False

    repeat: list[dict[str, object]] = []


class TestCaseConfig(BaseModel):
    name: str
    commands: list[CommandConfig] = []
    # FIXME: sandbox and maybe other settings?

    repeat: list[dict[str, object]] = []


class TestSuiteConfig(BaseModel):
    name: str
    instructor_files_needed: list[str] = []
    student_files_needed: list[str] = []
    test_cases: list[TestCaseConfig] = []


class ProjectSettings(BaseModel):
    name: str


class ProjectConfig(BaseModel):
    settings: ProjectSettings
    course: CourseData
    student_files: list[StudentFileConfig] = []
    instructor_files: list[InstructorFileConfig] = []
    test_suites: list[TestSuiteConfig] = []


class AGConfig(BaseModel):
    project: ProjectConfig
    feedback_presets: dict[str, AGTestCommandFeedbackConfig] = BUILTIN_FDBK_PRESETS
