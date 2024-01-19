"""
Set up autograder.io assignments using a yaml config file.
"""

import argparse
from ag_contrib.config.generated.schema import Semester

from ag_contrib.config.init_project import init_project
from ag_contrib.config.save_project import save_project


def main():
    args = parse_args()
    kwargs = vars(args)
    func = kwargs.pop('func')
    func(**kwargs)


def parse_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument('--base_url', '-u', type=str,
                        default='https://autograder.io/')
    parser.add_argument(
        '--token_file', '-t', type=str, default='.agtoken',
        help="A filename or a path describing where to find the API token. "
             "If a filename, searches the current directory and each "
             "directory up to and including the current user's home "
             "directory until the file is found.")

    tool_parsers = parser.add_subparsers(required=True)
    make_config_parser(tool_parsers)

    return parser.parse_args()


def make_config_parser(tool_parsers):
    config_parser = tool_parsers.add_parser('config')
    subparsers = config_parser.add_subparsers(required=True)

    init_project_parser = subparsers.add_parser('init_project')
    init_project_parser.add_argument('project_name')
    init_project_parser.add_argument('course_name')
    init_project_parser.add_argument('course_term', choices=[semester.value for semester in Semester])
    init_project_parser.add_argument('course_year')
    init_project_parser.add_argument('--config_file', '-f', default=DEFAULT_config_file)
    init_project_parser.set_defaults(func=init_project)

    save_project_parser = subparsers.add_parser('save_project')
    save_project_parser.add_argument('--config_file', '-f', default=DEFAULT_config_file)
    save_project_parser.set_defaults(func=save_project)


DEFAULT_config_file = 'ag_project.yml'


if __name__ == '__main__':
    main()
