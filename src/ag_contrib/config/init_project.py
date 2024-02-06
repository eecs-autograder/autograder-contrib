from pathlib import Path
import yaml

from ag_contrib.config.generated.schema import Semester
from ag_contrib.config.models import (
    AGConfig,
    CourseSelection,
    InstructorFileConfig,
    MultiCmdTestCaseConfig,
    MultiCommandConfig,
    ProjectConfig,
    SingleCmdTestCaseConfig,
    TestSuiteConfig,
)
from ag_contrib.config.generated import schema as ag_schema


def init_project(
    project_name: str,
    course_name: str,
    course_term: Semester,
    course_year: int,
    config_file: str,
    **kwargs: object,
):
    project = ProjectConfig(
        # FIXME: Make a project settings and course settings model
        name=project_name,
        course=CourseSelection(name=course_name, semester=course_term, year=course_year),
        student_files=[
            ag_schema.CreateExpectedStudentFile(
                pattern="hello.py", min_num_matches=1, max_num_matches=1
            )
        ],
        instructor_files=[InstructorFileConfig(local_path=Path("tests.py"))],
        test_suites=[
            TestSuiteConfig(
                name="Suite 1",
                test_cases=[
                    SingleCmdTestCaseConfig(name="Test 1", cmd='echo "Hello 1!"'),
                    MultiCmdTestCaseConfig(
                        name="Test 2",
                        commands=[MultiCommandConfig(name="Test 2", cmd='echo "Hello 2!"')],
                    ),
                ],
            )
        ],
    )

    with open(config_file, "w") as f:
        yaml.dump(AGConfig(project=project).model_dump(mode="json"), f, sort_keys=False)
