import yaml

from ag_contrib.config.generated.schema import Semester
from ag_contrib.config.models import (
    AGConfig,
    CommandConfig,
    CourseData,
    InstructorFileConfig,
    ProjectConfig,
    ProjectSettings,
    StudentFileConfig,
    TestCaseConfig,
    TestSuiteConfig,
)


def init_project(
    project_name: str,
    course_name: str,
    course_term: Semester,
    course_year: int,
    config_file: str,
    **kwargs: object,
):
    project = ProjectConfig(
        settings=ProjectSettings(name=project_name),
        course=CourseData(name=course_name, semester=course_term, year=course_year),
        # student_files=[StudentFileConfig(pattern="hello.py")],
        # instructor_files=[InstructorFileConfig(local_path="tests.py")],
        test_suites=[
            TestSuiteConfig(
                name="Suite 1",
                test_cases=[
                    TestCaseConfig(
                        name="Test 1",
                        commands=[
                            CommandConfig(
                                name="Test 1",
                                cmd='echo "Hello!"',
                            )
                        ],
                    )
                ],
            )
        ],
    )

    with open(config_file, "w") as f:
        yaml.dump(AGConfig(project=project).model_dump(mode="json"), f, sort_keys=False)
