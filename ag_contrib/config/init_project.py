from fastapi.encoders import jsonable_encoder
import yaml
from ag_contrib.config.generated.schema import Semester
from ag_contrib.config.models import CommandConfig, CourseData, ProjectConfig, TestCaseConfig, TestSuiteConfig


def init_project(
    project_name: str,
    course_name: str,
    course_term: Semester,
    course_year: int,
    config_filename: str,
    **kwargs: object,
):
    project = ProjectConfig(
        name=project_name,
        course=CourseData(name=course_name, semester=course_term, year=course_year),
        test_suites=[
            TestSuiteConfig(
                name='Suite 1',
                test_cases=[
                    TestCaseConfig(
                        name='Test 1',
                        commands=[
                            CommandConfig(
                                name='Test 1',
                                cmd='echo "Hello!"',
                            )
                        ],
                    )
                ],
            )
        ],
    )

    with open(config_filename, 'w') as f:
        yaml.dump(jsonable_encoder(project), f, sort_keys=False)
